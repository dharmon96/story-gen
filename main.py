"""
Main entry point for Film Generator App
Run this file to start the application
"""

import tkinter as tk
import sys
import traceback
from database import init_database
from gui import FilmGeneratorApp

def main():
    """Main application entry point"""
    try:
        # Initialize database
        print("Initializing database...")
        init_database()
        
        # Create main window
        print("Starting application...")
        root = tk.Tk()
        
        # Create application
        app = FilmGeneratorApp(root)
        
        # Handle window close
        def on_closing():
            print("Closing application...")
            app.cleanup()
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Start main loop
        root.mainloop()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
    finally:
        # Keep window open on Windows
        input("\nPress Enter to exit...")
