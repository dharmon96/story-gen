"""
Multi-Node Management System
Handles distributed processing across multiple PCs for both text LLM and ComfyUI tasks
"""

import json
import time
import threading
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
import requests

class NodeType(Enum):
    """Types of processing nodes"""
    TEXT_LLM = "text_llm"      # Ollama/LLM processing
    COMFYUI = "comfyui"        # Video generation
    HYBRID = "hybrid"          # Both text and ComfyUI

class NodeStatus(Enum):
    """Node availability status"""
    AVAILABLE = "available"
    BUSY_TEXT = "busy_text"
    BUSY_COMFYUI = "busy_comfyui"  
    BUSY_BOTH = "busy_both"
    OFFLINE = "offline"
    ERROR = "error"

class ProcessingTask:
    """Represents a processing task"""
    def __init__(self, task_id: str, task_type: str, step: str, priority: int = 5):
        self.task_id = task_id
        self.task_type = task_type  # 'text_llm' or 'comfyui'
        self.step = step  # AI generation step
        self.priority = priority
        self.created_at = datetime.now()
        self.assigned_node = None
        self.started_at = None
        self.completed_at = None
        self.status = "queued"
        self.result = None
        self.error = None

class ProcessingNode:
    """Represents a processing node (PC)"""
    def __init__(self, node_id: str, host: str, capabilities: List[NodeType]):
        self.node_id = node_id
        self.host = host
        self.capabilities = capabilities
        self.status = NodeStatus.AVAILABLE
        self.current_tasks = {"text_llm": None, "comfyui": None}
        self.last_heartbeat = datetime.now()
        self.total_completed = 0
        self.avg_processing_time = {}  # task_type -> avg_time
        self.load_score = 0.0  # Lower is better
        self.metadata = {}  # Additional node info (models, GPU info, etc.)
        
        # Ollama connection info
        self.ollama_port = 11434
        self.ollama_models = []
        
        # ComfyUI connection info
        self.comfyui_port = 8188
        self.comfyui_available = False

    def can_handle_task(self, task_type: str) -> bool:
        """Check if node can handle a specific task type"""
        if task_type == "text_llm":
            return (NodeType.TEXT_LLM in self.capabilities or 
                   NodeType.HYBRID in self.capabilities) and \
                   self.current_tasks["text_llm"] is None
        elif task_type == "comfyui":
            return (NodeType.COMFYUI in self.capabilities or 
                   NodeType.HYBRID in self.capabilities) and \
                   self.current_tasks["comfyui"] is None
        return False

    def assign_task(self, task: ProcessingTask) -> bool:
        """Assign a task to this node"""
        if not self.can_handle_task(task.task_type):
            return False
        
        self.current_tasks[task.task_type] = task
        task.assigned_node = self.node_id
        task.started_at = datetime.now()
        task.status = "processing"
        
        # Update node status
        self.update_status()
        return True

    def complete_task(self, task: ProcessingTask, result=None, error=None):
        """Mark task as completed"""
        if self.current_tasks.get(task.task_type) == task:
            self.current_tasks[task.task_type] = None
            task.completed_at = datetime.now()
            task.status = "completed" if result else "failed"
            task.result = result
            task.error = error
            
            # Update statistics
            if task.started_at:
                processing_time = (task.completed_at - task.started_at).total_seconds()
                if task.task_type not in self.avg_processing_time:
                    self.avg_processing_time[task.task_type] = processing_time
                else:
                    # Exponential moving average
                    self.avg_processing_time[task.task_type] = \
                        0.8 * self.avg_processing_time[task.task_type] + 0.2 * processing_time
            
            if result:
                self.total_completed += 1
            
            # Update node status
            self.update_status()

    def update_status(self):
        """Update node status based on current tasks"""
        text_busy = self.current_tasks["text_llm"] is not None
        comfyui_busy = self.current_tasks["comfyui"] is not None
        
        if text_busy and comfyui_busy:
            self.status = NodeStatus.BUSY_BOTH
        elif text_busy:
            self.status = NodeStatus.BUSY_TEXT
        elif comfyui_busy:
            self.status = NodeStatus.BUSY_COMFYUI
        else:
            self.status = NodeStatus.AVAILABLE

    def calculate_load_score(self) -> float:
        """Calculate load score for load balancing (lower is better)"""
        base_load = len([t for t in self.current_tasks.values() if t is not None])
        
        # Factor in historical performance
        avg_time = sum(self.avg_processing_time.values()) / max(1, len(self.avg_processing_time))
        
        # Factor in total completed tasks (more completed = better node)
        completion_bonus = min(self.total_completed * 0.1, 2.0)
        
        self.load_score = base_load + (avg_time / 60.0) - completion_bonus
        return self.load_score

class NodeManager:
    """Manages multiple processing nodes and task distribution"""
    
    def __init__(self):
        self.nodes: Dict[str, ProcessingNode] = {}
        self.task_queue: List[ProcessingTask] = []
        self.completed_tasks: List[ProcessingTask] = []
        self.step_assignments: Dict[str, List[str]] = {}  # step -> [node_ids]
        
        self._running = False
        self._queue_thread = None
        self._heartbeat_thread = None
        
        # Load balancing settings
        self.max_queue_size = 100
        self.heartbeat_interval = 30  # seconds
        self.node_timeout = 120  # seconds
        
    def start(self):
        """Start the node manager"""
        if not self._running:
            self._running = True
            self._queue_thread = threading.Thread(target=self._process_queue, daemon=True)
            self._heartbeat_thread = threading.Thread(target=self._heartbeat_monitor, daemon=True)
            
            self._queue_thread.start()
            self._heartbeat_thread.start()
            
            print("Node manager started")

    def stop(self):
        """Stop the node manager"""
        self._running = False
        if self._queue_thread:
            self._queue_thread.join(timeout=5)
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=5)
        print("Node manager stopped")

    def add_node(self, node_id: str, host: str, capabilities: List[NodeType]) -> ProcessingNode:
        """Add a new processing node"""
        node = ProcessingNode(node_id, host, capabilities)
        self.nodes[node_id] = node
        
        # Auto-discover node capabilities
        self._discover_node_capabilities(node)
        
        print(f"Added node {node_id} ({host}) with capabilities: {[c.value for c in capabilities]}")
        return node

    def remove_node(self, node_id: str):
        """Remove a processing node"""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            
            # Handle any active tasks
            for task_type, task in node.current_tasks.items():
                if task:
                    task.status = "failed"
                    task.error = f"Node {node_id} was removed"
                    self.completed_tasks.append(task)
            
            # Remove from step assignments
            for step, assigned_nodes in self.step_assignments.items():
                if node_id in assigned_nodes:
                    assigned_nodes.remove(node_id)
            
            del self.nodes[node_id]
            print(f"Removed node {node_id}")

    def assign_node_to_step(self, step: str, node_id: str):
        """Assign a node to handle a specific generation step"""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
        
        if step not in self.step_assignments:
            self.step_assignments[step] = []
        
        if node_id not in self.step_assignments[step]:
            self.step_assignments[step].append(node_id)
            print(f"Assigned node {node_id} to step {step}")

    def unassign_node_from_step(self, step: str, node_id: str):
        """Remove node assignment from a step"""
        if step in self.step_assignments and node_id in self.step_assignments[step]:
            self.step_assignments[step].remove(node_id)
            print(f"Unassigned node {node_id} from step {step}")

    def get_available_nodes_for_step(self, step: str, task_type: str) -> List[ProcessingNode]:
        """Get available nodes that can handle a specific step and task type"""
        assigned_node_ids = self.step_assignments.get(step, [])
        if not assigned_node_ids:
            # If no specific assignments, use any available node
            assigned_node_ids = list(self.nodes.keys())
        
        available_nodes = []
        for node_id in assigned_node_ids:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                if (node.status not in [NodeStatus.OFFLINE, NodeStatus.ERROR] and 
                    node.can_handle_task(task_type)):
                    available_nodes.append(node)
        
        # Sort by load score (lower is better)
        available_nodes.sort(key=lambda n: n.calculate_load_score())
        return available_nodes

    def submit_task(self, task_id: str, task_type: str, step: str, priority: int = 5) -> ProcessingTask:
        """Submit a new task to the queue"""
        if len(self.task_queue) >= self.max_queue_size:
            raise RuntimeError("Task queue is full")
        
        task = ProcessingTask(task_id, task_type, step, priority)
        
        # Insert task in priority order
        inserted = False
        for i, queued_task in enumerate(self.task_queue):
            if task.priority > queued_task.priority:
                self.task_queue.insert(i, task)
                inserted = True
                break
        
        if not inserted:
            self.task_queue.append(task)
        
        print(f"Submitted task {task_id} ({task_type}) for step {step}")
        return task

    def get_task_status(self, task_id: str) -> Optional[ProcessingTask]:
        """Get status of a specific task"""
        # Check active tasks
        for task in self.task_queue:
            if task.task_id == task_id:
                return task
        
        # Check active tasks on nodes
        for node in self.nodes.values():
            for task in node.current_tasks.values():
                if task and task.task_id == task_id:
                    return task
        
        # Check completed tasks
        for task in self.completed_tasks:
            if task.task_id == task_id:
                return task
        
        return None

    def _process_queue(self):
        """Process task queue in background thread"""
        while self._running:
            if self.task_queue:
                task = self.task_queue[0]
                
                # Find available node for this task
                available_nodes = self.get_available_nodes_for_step(task.step, task.task_type)
                
                if available_nodes:
                    # Assign to best available node
                    selected_node = available_nodes[0]
                    
                    if selected_node.assign_task(task):
                        self.task_queue.pop(0)  # Remove from queue
                        print(f"Assigned task {task.task_id} to node {selected_node.node_id}")
                        
                        # Start task execution in separate thread
                        threading.Thread(
                            target=self._execute_task, 
                            args=(task, selected_node), 
                            daemon=True
                        ).start()
                    else:
                        print(f"Failed to assign task {task.task_id} to node {selected_node.node_id}")
            
            time.sleep(1)  # Check queue every second

    def _execute_task(self, task: ProcessingTask, node: ProcessingNode):
        """Execute a task on a specific node"""
        try:
            if task.task_type == "text_llm":
                result = self._execute_text_llm_task(task, node)
            elif task.task_type == "comfyui":
                result = self._execute_comfyui_task(task, node)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
            
            node.complete_task(task, result=result)
            self.completed_tasks.append(task)
            print(f"Completed task {task.task_id} on node {node.node_id}")
            
        except Exception as e:
            error_msg = str(e)
            node.complete_task(task, error=error_msg)
            self.completed_tasks.append(task)
            print(f"Task {task.task_id} failed on node {node.node_id}: {error_msg}")

    def _execute_text_llm_task(self, task: ProcessingTask, node: ProcessingNode) -> str:
        """Execute text LLM task on node"""
        # This would integrate with the actual text generation
        # For now, return simulated result
        time.sleep(2)  # Simulate processing time
        return f"Simulated text LLM result for task {task.task_id} on node {node.node_id}"

    def _execute_comfyui_task(self, task: ProcessingTask, node: ProcessingNode) -> str:
        """Execute ComfyUI task on node"""
        # This would integrate with ComfyUI API
        # For now, return simulated result
        time.sleep(5)  # Simulate processing time
        return f"Simulated ComfyUI result for task {task.task_id} on node {node.node_id}"

    def _heartbeat_monitor(self):
        """Monitor node heartbeats and update status"""
        while self._running:
            current_time = datetime.now()
            
            for node in self.nodes.values():
                # Check if node is responsive
                time_since_heartbeat = (current_time - node.last_heartbeat).total_seconds()
                
                if time_since_heartbeat > self.node_timeout:
                    if node.status != NodeStatus.OFFLINE:
                        print(f"Node {node.node_id} appears offline")
                        node.status = NodeStatus.OFFLINE
                        
                        # Handle any active tasks
                        for task_type, task in node.current_tasks.items():
                            if task:
                                task.status = "failed"
                                task.error = f"Node {node.node_id} went offline"
                                self.completed_tasks.append(task)
                                node.current_tasks[task_type] = None
                else:
                    # Try to ping node
                    if self._ping_node(node):
                        node.last_heartbeat = current_time
                        if node.status == NodeStatus.OFFLINE:
                            print(f"Node {node.node_id} back online")
                            node.update_status()
            
            time.sleep(self.heartbeat_interval)

    def _ping_node(self, node: ProcessingNode) -> bool:
        """Ping a node to check if it's responsive"""
        try:
            # Try Ollama API
            if NodeType.TEXT_LLM in node.capabilities or NodeType.HYBRID in node.capabilities:
                response = requests.get(f"http://{node.host}:{node.ollama_port}/api/tags", timeout=5)
                if response.status_code == 200:
                    return True
            
            # Try ComfyUI API
            if NodeType.COMFYUI in node.capabilities or NodeType.HYBRID in node.capabilities:
                response = requests.get(f"http://{node.host}:{node.comfyui_port}/system_stats", timeout=5)
                if response.status_code == 200:
                    return True
            
            return False
            
        except Exception:
            return False

    def _discover_node_capabilities(self, node: ProcessingNode):
        """Auto-discover what services are available on a node"""
        # Check for Ollama
        try:
            response = requests.get(f"http://{node.host}:{node.ollama_port}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                node.ollama_models = [model['name'] for model in data.get('models', [])]
                print(f"Node {node.node_id}: Found {len(node.ollama_models)} Ollama models")
        except Exception:
            pass
        
        # Check for ComfyUI
        try:
            response = requests.get(f"http://{node.host}:{node.comfyui_port}/system_stats", timeout=5)
            if response.status_code == 200:
                node.comfyui_available = True
                print(f"Node {node.node_id}: ComfyUI available")
        except Exception:
            pass

    def get_node_statistics(self) -> Dict:
        """Get statistics about all nodes"""
        stats = {
            'total_nodes': len(self.nodes),
            'online_nodes': len([n for n in self.nodes.values() if n.status != NodeStatus.OFFLINE]),
            'available_nodes': len([n for n in self.nodes.values() if n.status == NodeStatus.AVAILABLE]),
            'busy_nodes': len([n for n in self.nodes.values() if 'BUSY' in n.status.value]),
            'queued_tasks': len(self.task_queue),
            'completed_tasks': len(self.completed_tasks),
            'step_assignments': dict(self.step_assignments),
            'node_details': {}
        }
        
        for node_id, node in self.nodes.items():
            stats['node_details'][node_id] = {
                'host': node.host,
                'status': node.status.value,
                'capabilities': [c.value for c in node.capabilities],
                'current_tasks': {k: v.task_id if v else None for k, v in node.current_tasks.items()},
                'total_completed': node.total_completed,
                'avg_processing_time': node.avg_processing_time,
                'load_score': node.calculate_load_score(),
                'ollama_models': node.ollama_models,
                'comfyui_available': node.comfyui_available
            }
        
        return stats