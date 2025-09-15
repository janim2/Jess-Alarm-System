import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import datetime
import pygame
import os
from typing import List, Dict, Optional

class AlarmClock:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dynamic Alarm Clock")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Initialize pygame mixer for sound
        pygame.mixer.init()
        
        # Alarm storage
        self.alarms: List[Dict] = []
        self.alarm_threads: List[threading.Thread] = []
        self.running_alarms: List[bool] = []
        
        # Create default alarm sound (simple beep)
        self.create_default_sound()
        
        self.setup_ui()
        self.update_clock()
        
    def create_default_sound(self):
        """Create a default beep sound file if none exists"""
        try:
            # Generate a simple tone using pygame
            import numpy as np
            
            # Create a simple beep sound
            sample_rate = 22050
            duration = 1.0  # seconds
            frequency = 800  # Hz
            
            frames = int(duration * sample_rate)
            arr = np.zeros(frames)
            
            for i in range(frames):
                arr[i] = np.sin(2 * np.pi * frequency * i / sample_rate)
            
            # Convert to 16-bit integers
            arr = (arr * 32767).astype(np.int16)
            
            # Create stereo sound
            stereo_arr = np.zeros((frames, 2), dtype=np.int16)
            stereo_arr[:, 0] = arr
            stereo_arr[:, 1] = arr
            
            # Save as default sound
            self.default_sound = pygame.sndarray.make_sound(stereo_arr)
            
        except ImportError:
            # If numpy is not available, we'll use pygame's built-in capabilities
            self.default_sound = None
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Current time display
        self.time_label = ttk.Label(main_frame, text="", font=("Arial", 24, "bold"))
        self.time_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Alarm creation section
        ttk.Label(main_frame, text="Create New Alarm", font=("Arial", 14, "bold")).grid(row=1, column=0, columnspan=3, pady=(0, 10))
        
        # Time input frame
        time_frame = ttk.Frame(main_frame)
        time_frame.grid(row=2, column=0, columnspan=3, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(time_frame, text="Hour:").grid(row=0, column=0, padx=(0, 5))
        self.hour_var = tk.StringVar(value="12")
        self.hour_spinbox = ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.hour_var, width=5)
        self.hour_spinbox.grid(row=0, column=1, padx=5)
        
        ttk.Label(time_frame, text="Minute:").grid(row=0, column=2, padx=(20, 5))
        self.minute_var = tk.StringVar(value="27")
        self.minute_spinbox = ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.minute_var, width=5)
        self.minute_spinbox.grid(row=0, column=3, padx=5)
        
        # Alarm type selection
        type_frame = ttk.Frame(main_frame)
        type_frame.grid(row=3, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(type_frame, text="Alarm Type:").grid(row=0, column=0, padx=(0, 10))
        self.alarm_type = tk.StringVar(value="daily")
        ttk.Radiobutton(type_frame, text="Daily", variable=self.alarm_type, value="daily").grid(row=0, column=1, padx=5)
        ttk.Radiobutton(type_frame, text="Once", variable=self.alarm_type, value="once").grid(row=0, column=2, padx=5)
        ttk.Radiobutton(type_frame, text="Every Hour", variable=self.alarm_type, value="hourly").grid(row=0, column=3, padx=5)
        
        # Alarm label
        label_frame = ttk.Frame(main_frame)
        label_frame.grid(row=4, column=0, columnspan=3, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(label_frame, text="Label:").grid(row=0, column=0, padx=(0, 10))
        self.label_var = tk.StringVar(value="Alarm")
        self.label_entry = ttk.Entry(label_frame, textvariable=self.label_var, width=30)
        self.label_entry.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        label_frame.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=15)
        
        ttk.Button(button_frame, text="Add Alarm", command=self.add_alarm).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Test Sound", command=self.test_sound).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Stop All Alarms", command=self.stop_all_alarms).grid(row=0, column=2, padx=5)
        
        # Alarm list
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=6, column=0, columnspan=3, pady=(20, 0), sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        ttk.Label(list_frame, text="Active Alarms", font=("Arial", 12, "bold")).grid(row=0, column=0, pady=(0, 10))
        
        # Treeview for alarm list
        self.alarm_tree = ttk.Treeview(list_frame, columns=("Time", "Type", "Label", "Status"), show="headings", height=8)
        self.alarm_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure columns
        self.alarm_tree.heading("Time", text="Time")
        self.alarm_tree.heading("Type", text="Type")
        self.alarm_tree.heading("Label", text="Label")
        self.alarm_tree.heading("Status", text="Status")
        
        self.alarm_tree.column("Time", width=100)
        self.alarm_tree.column("Type", width=100)
        self.alarm_tree.column("Label", width=200)
        self.alarm_tree.column("Status", width=100)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.alarm_tree.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.alarm_tree.configure(yscrollcommand=scrollbar.set)
        
        # Delete button
        ttk.Button(list_frame, text="Delete Selected", command=self.delete_alarm).grid(row=2, column=0, pady=10)
        
    def update_clock(self):
        """Update the current time display"""
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.time_label.config(text=f"{current_date}\n{current_time}")
        self.root.after(1000, self.update_clock)
        
    def add_alarm(self):
        """Add a new alarm"""
        try:
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            alarm_type = self.alarm_type.get()
            label = self.label_var.get().strip() or "Alarm"
            
            if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                messagebox.showerror("Invalid Time", "Please enter valid hour (0-23) and minute (0-59)")
                return
                
            alarm = {
                "id": len(self.alarms),
                "hour": hour,
                "minute": minute,
                "type": alarm_type,
                "label": label,
                "active": True,
                "triggered_today": False
            }
            
            self.alarms.append(alarm)
            self.running_alarms.append(True)
            
            # Start alarm thread
            alarm_thread = threading.Thread(target=self.monitor_alarm, args=(alarm["id"],), daemon=True)
            self.alarm_threads.append(alarm_thread)
            alarm_thread.start()
            
            self.update_alarm_list()
            messagebox.showinfo("Alarm Added", f"Alarm set for {hour:02d}:{minute:02d} ({alarm_type})")
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for hour and minute")
            
    def monitor_alarm(self, alarm_id: int):
        """Monitor a specific alarm in a separate thread"""
        while alarm_id < len(self.running_alarms) and self.running_alarms[alarm_id]:
            try:
                if alarm_id >= len(self.alarms):
                    break
                    
                alarm = self.alarms[alarm_id]
                if not alarm["active"]:
                    time.sleep(1)
                    continue
                
                current_time = datetime.datetime.now()
                current_hour = current_time.hour
                current_minute = current_time.minute
                current_date = current_time.date()
                
                should_trigger = False
                
                if alarm["type"] == "hourly":
                    # Trigger at the specified minute of every hour
                    if current_minute == alarm["minute"]:
                        should_trigger = True
                        
                elif alarm["type"] == "daily":
                    # Trigger once per day at the specified time
                    if (current_hour == alarm["hour"] and 
                        current_minute == alarm["minute"] and 
                        not alarm["triggered_today"]):
                        should_trigger = True
                        alarm["triggered_today"] = True
                        
                    # Reset daily trigger at midnight
                    if current_hour == 0 and current_minute == 0:
                        alarm["triggered_today"] = False
                        
                elif alarm["type"] == "once":
                    # Trigger once at the specified time
                    if (current_hour == alarm["hour"] and 
                        current_minute == alarm["minute"]):
                        should_trigger = True
                        alarm["active"] = False  # Deactivate after triggering
                
                if should_trigger:
                    self.trigger_alarm(alarm)
                    self.root.after(0, self.update_alarm_list)  # Update UI in main thread
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Error in alarm monitoring: {e}")
                time.sleep(1)
                
    def trigger_alarm(self, alarm: Dict):
        """Trigger the alarm"""
        print(f"🚨 ALARM TRIGGERED: {alarm['label']} at {alarm['hour']:02d}:{alarm['minute']:02d}")
        
        try:
            # Play sound in separate thread to not block
            sound_thread = threading.Thread(target=self.play_alarm_sound, daemon=True)
            sound_thread.start()
            
            # Show popup
            self.root.after(0, lambda: self.show_alarm_popup(alarm))
            
        except Exception as e:
            print(f"Error triggering alarm: {e}")
            
    def play_alarm_sound(self):
        """Play the alarm sound"""
        try:
            if self.default_sound:
                # Play the generated sound
                self.default_sound.play(loops=3)  # Play 3 times
            else:
                # Fallback: try to play system beep
                try:
                    import winsound
                    for _ in range(3):
                        winsound.Beep(800, 1000)  # 800Hz for 1 second
                except ImportError:
                    # Last resort: print beep character
                    for _ in range(5):
                        print("\a", end="", flush=True)
                        time.sleep(0.5)
        except Exception as e:
            print(f"Could not play alarm sound: {e}")
            
    def show_alarm_popup(self, alarm: Dict):
        """Show alarm popup dialog"""
        result = messagebox.showinfo(
            "ALARM!", 
            f"⏰ {alarm['label']}\n\nTime: {alarm['hour']:02d}:{alarm['minute']:02d}\nType: {alarm['type']}",
            type=messagebox.OK
        )
        
    def test_sound(self):
        """Test the alarm sound"""
        try:
            self.play_alarm_sound()
            messagebox.showinfo("Sound Test", "Playing alarm sound...")
        except Exception as e:
            messagebox.showerror("Sound Error", f"Could not play sound: {e}")
            
    def delete_alarm(self):
        """Delete selected alarm"""
        selection = self.alarm_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an alarm to delete")
            return
            
        item = selection[0]
        alarm_id = int(self.alarm_tree.item(item)["values"][0])  # Assuming ID is stored somewhere
        
        # Find and remove alarm
        for i, alarm in enumerate(self.alarms):
            if i == alarm_id or alarm.get("display_index") == alarm_id:
                self.alarms[i]["active"] = False
                if i < len(self.running_alarms):
                    self.running_alarms[i] = False
                break
                
        self.update_alarm_list()
        messagebox.showinfo("Alarm Deleted", "Selected alarm has been deleted")
        
    def stop_all_alarms(self):
        """Stop all active alarms"""
        for i in range(len(self.running_alarms)):
            self.running_alarms[i] = False
        for alarm in self.alarms:
            alarm["active"] = False
        pygame.mixer.stop()  # Stop any currently playing sounds
        self.update_alarm_list()
        messagebox.showinfo("All Alarms Stopped", "All alarms have been deactivated")
        
    def update_alarm_list(self):
        """Update the alarm list display"""
        # Clear existing items
        for item in self.alarm_tree.get_children():
            self.alarm_tree.delete(item)
            
        # Add current alarms
        for i, alarm in enumerate(self.alarms):
            if alarm["active"]:
                time_str = f"{alarm['hour']:02d}:{alarm['minute']:02d}"
                status = "Active" if alarm["active"] else "Inactive"
                
                # Store index for deletion
                alarm["display_index"] = i
                
                self.alarm_tree.insert("", "end", values=(i, time_str, alarm["type"], alarm["label"], status))
                
    def run(self):
        """Start the application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.stop_all_alarms()
        finally:
            pygame.mixer.quit()

if __name__ == "__main__":
    # Check for required dependencies
    required_modules = ["pygame", "numpy"]
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("Missing required modules. Please install:")
        for module in missing_modules:
            print(f"  pip install {module}")
        print("\nInstalling pygame is required for sound playback.")
        print("Installing numpy is recommended for better sound generation.")
        exit(1)
    
    # Create and run the alarm clock
    app = AlarmClock()
    app.run()