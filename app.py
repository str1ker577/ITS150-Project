import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import numpy as np
import random
import threading
import time
from collections import deque
import statistics

class Process:
    """Process Control Block (PCB) - represents a process in the system"""
    def __init__(self, arrival_time, process_id):
        self.process_id = process_id
        self.arrival_time = arrival_time
        self.burst_time = None  # Total CPU time needed
        self.remaining_time = None  # For preemptive algorithms
        self.priority = None  # For priority scheduling
        self.start_time = None  # When process first gets CPU
        self.completion_time = None  # When process finishes
        self.waiting_time = 0  # Time spent in ready queue
        self.turnaround_time = 0  # Total time from arrival to completion
        self.response_time = None  # Time from arrival to first execution
        self.state = "NEW"  # NEW, READY, RUNNING, TERMINATED

class ProcessSchedulerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Process Scheduling Simulator")
        self.root.state('zoomed')  # Start maximized on Windows
        self.root.configure(bg='#f8f9fa')
        self.root.minsize(1200, 800)  # Set minimum size
        
        # Configure modern color scheme
        self.colors = {
            'primary': '#2c3e50',
            'secondary': '#3498db', 
            'success': '#27ae60',
            'warning': '#f39c12',
            'danger': '#e74c3c',
            'light': '#ecf0f1',
            'dark': '#2c3e50',
            'accent': '#9b59b6'
        }
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Simulation parameters
        self.simulation_running = False
        self.simulation_thread = None
        self.current_time = 0
        self.processes = []
        self.completed_processes = []
        
        # Animation data
        self.time_points = []
        self.ready_queue_data = []
        self.gantt_data = []  # For Gantt chart: [(start_time, process_id, duration)]
        self.animation = None  # Initialize animation variable
        
        self.setup_gui()
    
    def on_closing(self):
        """Handle window close event"""
        # Stop any running simulation
        self.simulation_running = False
        
        # Stop animation
        if hasattr(self, 'animation') and self.animation:
            try:
                self.animation.event_source.stop()
            except:
                pass
            self.animation = None
        
        # Wait for simulation thread to finish
        if hasattr(self, 'simulation_thread') and self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=1)
        
        # Destroy the window
        self.root.destroy()
        
    def setup_gui(self):
        # Create main frames with proper responsive layout
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill='x', padx=15, pady=10)
        
        viz_frame = ttk.Frame(self.root)
        viz_frame.pack(fill='both', expand=True, padx=15, pady=(0, 10))
        
        # Configure grid weights for responsiveness
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(1, weight=1)
        control_frame.grid_columnconfigure(2, weight=1)
        control_frame.grid_columnconfigure(3, weight=1)
        
        # Control Panel Header
        header_frame = ttk.Frame(control_frame)
        header_frame.grid(row=0, column=0, columnspan=4, sticky='ew', pady=(10, 15))
        header_frame.configure(style='Header.TFrame')
        
        title_label = ttk.Label(header_frame, text="Process Scheduling Simulator", 
                               font=('Segoe UI', 20, 'bold'))
        title_label.pack()
        
        subtitle_label = ttk.Label(header_frame, text="Advanced CPU Scheduling Algorithm Visualization", 
                                  font=('Segoe UI', 10), foreground='#7f8c8d')
        subtitle_label.pack()
        
        # Input parameters - Better organized layout
        params_frame = ttk.LabelFrame(control_frame, text="Simulation Parameters", padding=20)
        params_frame.grid(row=1, column=0, columnspan=4, sticky='ew', pady=10)
        params_frame.configure(style='Card.TLabelframe')
        
        # Create two columns for better organization
        left_frame = ttk.Frame(params_frame)
        left_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 20))
        
        right_frame = ttk.Frame(params_frame)
        right_frame.grid(row=0, column=1, sticky='nsew')
        
        # Left column
        ttk.Label(left_frame, text="Number of Processes:", font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky='w', pady=8)
        self.num_processes_var = tk.StringVar(value="10")
        ttk.Entry(left_frame, textvariable=self.num_processes_var, width=12, font=('Segoe UI', 10)).grid(row=0, column=1, padx=(10, 0), pady=8, sticky='w')
        
        ttk.Label(left_frame, text="Burst Time (ms):", font=('Segoe UI', 10, 'bold')).grid(row=1, column=0, sticky='w', pady=8)
        self.burst_min_var = tk.StringVar(value="10")
        self.burst_max_var = tk.StringVar(value="50")
        ttk.Entry(left_frame, textvariable=self.burst_min_var, width=8, font=('Segoe UI', 10)).grid(row=1, column=1, padx=(10, 5), pady=8, sticky='w')
        ttk.Label(left_frame, text="to", font=('Segoe UI', 10)).grid(row=1, column=2, pady=8)
        ttk.Entry(left_frame, textvariable=self.burst_max_var, width=8, font=('Segoe UI', 10)).grid(row=1, column=3, padx=(5, 0), pady=8, sticky='w')
        
        ttk.Label(left_frame, text="Time Quantum (RR):", font=('Segoe UI', 10, 'bold')).grid(row=2, column=0, sticky='w', pady=8)
        self.quantum_var = tk.StringVar(value="5")
        ttk.Entry(left_frame, textvariable=self.quantum_var, width=12, font=('Segoe UI', 10)).grid(row=2, column=1, padx=(10, 5), pady=8, sticky='w')
        ttk.Label(left_frame, text="ms", font=('Segoe UI', 10)).grid(row=2, column=2, pady=8)
        
        # Right column
        ttk.Label(right_frame, text="Arrival Time (ms):", font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky='w', pady=8)
        self.arrival_min_var = tk.StringVar(value="0")
        self.arrival_max_var = tk.StringVar(value="50")
        ttk.Entry(right_frame, textvariable=self.arrival_min_var, width=8, font=('Segoe UI', 10)).grid(row=0, column=1, padx=(10, 5), pady=8, sticky='w')
        ttk.Label(right_frame, text="to", font=('Segoe UI', 10)).grid(row=0, column=2, pady=8)
        ttk.Entry(right_frame, textvariable=self.arrival_max_var, width=8, font=('Segoe UI', 10)).grid(row=0, column=3, padx=(5, 0), pady=8, sticky='w')
        
        ttk.Label(right_frame, text="Priority Range:", font=('Segoe UI', 10, 'bold')).grid(row=1, column=0, sticky='w', pady=8)
        self.priority_min_var = tk.StringVar(value="1")
        self.priority_max_var = tk.StringVar(value="5")
        ttk.Entry(right_frame, textvariable=self.priority_min_var, width=8, font=('Segoe UI', 10)).grid(row=1, column=1, padx=(10, 5), pady=8, sticky='w')
        ttk.Label(right_frame, text="to", font=('Segoe UI', 10)).grid(row=1, column=2, pady=8)
        ttk.Entry(right_frame, textvariable=self.priority_max_var, width=8, font=('Segoe UI', 10)).grid(row=1, column=3, padx=(5, 0), pady=8, sticky='w')
        
        # Algorithm selection - Better organized
        algo_frame = ttk.LabelFrame(control_frame, text="Scheduling Algorithm", padding=20)
        algo_frame.grid(row=2, column=0, columnspan=4, sticky='ew', pady=10)
        algo_frame.configure(style='Card.TLabelframe')
        
        # Configure grid weights for algorithms
        for i in range(3):
            algo_frame.grid_columnconfigure(i, weight=1)
        
        self.algorithm_var = tk.StringVar(value="fcfs")
        algorithms = [
            ("FCFS (First Come First Serve)", "fcfs"),
            ("SJF (Shortest Job First)", "sjf"),
            ("SRTF (Shortest Remaining Time First)", "srtf"),
            ("Round Robin", "rr"),
            ("Priority Scheduling (Non-Preemptive)", "priority"),
            ("Priority Scheduling (Preemptive)", "priority_preemptive")
        ]
        
        for i, (text, value) in enumerate(algorithms):
            row = i // 3
            col = i % 3
            radio = ttk.Radiobutton(algo_frame, text=text, variable=self.algorithm_var, 
                                  value=value)
            radio.grid(row=row, column=col, padx=15, pady=10, sticky='w')
        
        # Control buttons - Better layout
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=3, column=0, columnspan=4, pady=20)
        
        # Configure button frame grid
        for i in range(3):
            button_frame.grid_columnconfigure(i, weight=1)
        
        self.start_btn = ttk.Button(button_frame, text="▶ Start Simulation", 
                                    command=self.start_simulation, style='Success.TButton')
        self.start_btn.grid(row=0, column=0, padx=15, ipadx=20, ipady=10, sticky='ew')
        
        self.stop_btn = ttk.Button(button_frame, text="⏹ Stop", 
                                   command=self.stop_simulation, state='disabled', style='Danger.TButton')
        self.stop_btn.grid(row=0, column=1, padx=15, ipadx=20, ipady=10, sticky='ew')
        
        self.reset_btn = ttk.Button(button_frame, text="🔄 Reset", 
                                    command=self.reset_simulation, style='Warning.TButton')
        self.reset_btn.grid(row=0, column=2, padx=15, ipadx=20, ipady=10, sticky='ew')
        
        # Status - Better styling
        self.status_var = tk.StringVar(value="Ready to simulate")
        status_frame = ttk.Frame(control_frame)
        status_frame.grid(row=4, column=0, columnspan=4, pady=15, sticky='ew')
        status_frame.configure(style='Status.TFrame')
        
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                               font=('Segoe UI', 12, 'bold'), foreground='#2c3e50')
        status_label.pack()
        
        # Configure custom styles
        self.configure_styles()
        
        # Create visualization area
        self.setup_visualizations(viz_frame)
    
    def configure_styles(self):
        """Configure custom ttk styles for better UI"""
        style = ttk.Style()
        
        # Configure button styles with better contrast
        style.configure('Success.TButton', 
                       background='#27ae60', 
                       foreground='white',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(15, 8),
                       borderwidth=2,
                       relief='raised')
        
        style.map('Success.TButton',
                 background=[('active', '#2ecc71'), ('pressed', '#229954')])
        
        style.configure('Danger.TButton', 
                       background='#e74c3c', 
                       foreground='white',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(15, 8),
                       borderwidth=2,
                       relief='raised')
        
        style.map('Danger.TButton',
                 background=[('active', '#ec7063'), ('pressed', '#c0392b')])
        
        style.configure('Warning.TButton', 
                       background='#f39c12', 
                       foreground='white',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(15, 8),
                       borderwidth=2,
                       relief='raised')
        
        style.map('Warning.TButton',
                 background=[('active', '#f7dc6f'), ('pressed', '#d68910')])
        
        # Configure labelframe styles
        style.configure('Card.TLabelframe', 
                       background='white',
                       borderwidth=1,
                       relief='solid')
        
        style.configure('Card.TLabelframe.Label', 
                       background='white',
                       foreground=self.colors['primary'],
                       font=('Segoe UI', 10, 'bold'))
        
        # Configure entry styles
        style.configure('Modern.TEntry',
                       fieldbackground='white',
                       borderwidth=1,
                       relief='solid',
                       font=('Segoe UI', 9))
        
        # Configure radiobutton styles
        style.configure('TRadiobutton',
                       font=('Segoe UI', 10))
        
        # Configure label styles
        style.configure('TLabel',
                       font=('Segoe UI', 9))
        
        # Configure status frame
        style.configure('Status.TFrame',
                       background='#ecf0f1',
                       borderwidth=1,
                       relief='solid')
        
    def setup_visualizations(self, parent):
        # Create notebook for different views
        notebook = ttk.Notebook(parent)
        notebook.pack(fill='both', expand=True)
        
        # Real-time simulation tab
        sim_frame = ttk.Frame(notebook)
        notebook.add(sim_frame, text="Live Simulation")
        
        # Gantt chart tab
        gantt_frame = ttk.Frame(notebook)
        notebook.add(gantt_frame, text="Gantt Chart")
        
        # Results tab
        results_frame = ttk.Frame(notebook)
        notebook.add(results_frame, text="Performance Analysis")
        
        # Memory OS Comparison tab
        memory_frame = ttk.Frame(notebook)
        notebook.add(memory_frame, text="Memory OS Analysis")
        
        # Setup live simulation visualization
        self.fig_live, (self.ax_ready_queue, self.ax_timeline) = plt.subplots(2, 1, figsize=(12, 7))
        self.fig_live.suptitle('Live Process Scheduling Simulation', fontsize=16, fontweight='bold', color='#2c3e50')
        self.fig_live.patch.set_facecolor('#f8f9fa')
        plt.subplots_adjust(hspace=0.4)
        
        self.canvas_live = FigureCanvasTkAgg(self.fig_live, sim_frame)
        self.canvas_live.get_tk_widget().pack(fill='both', expand=True)
        
        # Setup ready queue plot
        self.ax_ready_queue.set_title('Ready Queue Length Over Time', fontsize=12, fontweight='bold', color='#2c3e50')
        self.ax_ready_queue.set_xlabel('Time (ms)', fontsize=10, color='#34495e')
        self.ax_ready_queue.set_ylabel('Processes in Ready Queue', fontsize=10, color='#34495e')
        self.ax_ready_queue.grid(True, alpha=0.3, color='#bdc3c7')
        self.ax_ready_queue.set_facecolor('#ffffff')
        
        # Setup timeline plot
        self.ax_timeline.set_title('Process Execution Timeline', fontsize=12, fontweight='bold', color='#2c3e50')
        self.ax_timeline.set_xlabel('Time (ms)', fontsize=10, color='#34495e')
        self.ax_timeline.set_ylabel('Cumulative Processes Completed', fontsize=10, color='#34495e')
        self.ax_timeline.grid(True, alpha=0.3, color='#bdc3c7')
        self.ax_timeline.set_facecolor('#ffffff')
        
        # Setup Gantt chart
        self.fig_gantt, self.ax_gantt = plt.subplots(figsize=(12, 6))
        self.fig_gantt.suptitle('Process Execution Gantt Chart', fontsize=16, fontweight='bold', color='#2c3e50')
        self.fig_gantt.patch.set_facecolor('#f8f9fa')
        
        self.canvas_gantt = FigureCanvasTkAgg(self.fig_gantt, gantt_frame)
        self.canvas_gantt.get_tk_widget().pack(fill='both', expand=True)
        
        # Setup results visualization
        self.fig_results, ((self.ax_throughput, self.ax_waiting), 
                          (self.ax_turnaround, self.ax_response)) = plt.subplots(2, 2, figsize=(12, 8))
        self.fig_results.suptitle('Scheduling Performance Analysis', fontsize=16, fontweight='bold', color='#2c3e50')
        self.fig_results.patch.set_facecolor('#f8f9fa')
        plt.subplots_adjust(hspace=0.4, wspace=0.3)
        
        self.canvas_results = FigureCanvasTkAgg(self.fig_results, results_frame)
        self.canvas_results.get_tk_widget().pack(fill='both', expand=True)
        
        # Results text area
        self.results_text = tk.Text(results_frame, height=12, font=('Consolas', 9), 
                                   bg='#ffffff', fg='#2c3e50', relief='solid', borderwidth=1)
        self.results_text.pack(fill='x', padx=15, pady=10)
        
        # Setup Memory OS Analysis
        self.setup_memory_analysis(memory_frame)
        
    def start_simulation(self):
        try:
            # Validate inputs
            num_processes = int(self.num_processes_var.get())
            arrival_min = int(self.arrival_min_var.get())
            arrival_max = int(self.arrival_max_var.get())
            burst_min = int(self.burst_min_var.get())
            burst_max = int(self.burst_max_var.get())
            priority_min = int(self.priority_min_var.get())
            priority_max = int(self.priority_max_var.get())
            quantum = int(self.quantum_var.get())
            
            # Comprehensive validation
            if arrival_min > arrival_max or burst_min > burst_max or priority_min > priority_max:
                messagebox.showerror("Error", "Min values must be ≤ max values")
                return
                
            if num_processes < 1 or num_processes > 100:
                messagebox.showerror("Error", "Number of processes must be between 1 and 100")
                return
                
            if arrival_min < 0 or arrival_max < 0:
                messagebox.showerror("Error", "Arrival times must be non-negative")
                return
                
            if burst_min <= 0 or burst_max <= 0:
                messagebox.showerror("Error", "Burst times must be positive")
                return
                
            if priority_min <= 0 or priority_max <= 0:
                messagebox.showerror("Error", "Priority values must be positive")
                return
                
            if quantum <= 0:
                messagebox.showerror("Error", "Time quantum must be positive")
                return
                
            # Check for reasonable ranges
            if burst_max > 1000:
                messagebox.showerror("Error", "Burst time too large (max 1000ms)")
                return
                
            if arrival_max > 10000:
                messagebox.showerror("Error", "Arrival time too large (max 10000ms)")
                return
                
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")
            return
        
        # Reset data
        self.reset_data()
        
        # Update UI
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.simulation_running = True
        
        # Start simulation in separate thread
        self.simulation_thread = threading.Thread(
            target=self.run_simulation,
            args=(num_processes, arrival_min, arrival_max, burst_min, burst_max, 
                  priority_min, priority_max, quantum)
        )
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
        
        # Start animation with proper parameters
        if hasattr(self, 'animation') and self.animation:
            try:
                self.animation.event_source.stop()
            except:
                pass
            self.animation = None
        
        # Create animation that will persist
        self.animation = FuncAnimation(self.fig_live, self.update_plots, interval=200, 
                                     blit=False, cache_frame_data=False, save_count=1000, repeat=True)
        
    def stop_simulation(self):
        self.simulation_running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_var.set("Simulation stopped")
        
        if hasattr(self, 'animation') and self.animation:
            try:
                self.animation.event_source.stop()
            except:
                pass
            self.animation = None
            
    def reset_simulation(self):
        self.stop_simulation()
        self.reset_data()
        self.clear_plots()
        self.status_var.set("Ready to simulate")
        
        # Clear any existing animation
        if hasattr(self, 'animation') and self.animation:
            self.animation = None
        
    def reset_data(self):
        self.current_time = 0
        self.processes = []
        self.completed_processes = []
        self.time_points = []
        self.ready_queue_data = []
        self.gantt_data = []
        
    def clear_plots(self):
        for ax in [self.ax_ready_queue, self.ax_timeline, self.ax_gantt]:
            ax.clear()
        
        self.ax_ready_queue.set_title('Ready Queue Length Over Time')
        self.ax_ready_queue.set_xlabel('Time (ms)')
        self.ax_ready_queue.set_ylabel('Processes in Ready Queue')
        self.ax_ready_queue.grid(True, alpha=0.3)
        
        self.ax_timeline.set_title('Process Execution Timeline')
        self.ax_timeline.set_xlabel('Time (ms)')
        self.ax_timeline.set_ylabel('Cumulative Processes Completed')
        self.ax_timeline.grid(True, alpha=0.3)
        
        self.canvas_live.draw()
        self.canvas_gantt.draw()
        
    def generate_processes(self, num_processes, arrival_min, arrival_max, 
                          burst_min, burst_max, priority_min, priority_max):
        """Generate random processes with PCB attributes"""
        processes = []
        
        for i in range(1, num_processes + 1):
            arrival_time = random.randint(arrival_min, arrival_max)
            burst_time = random.randint(burst_min, burst_max)
            priority = random.randint(priority_min, priority_max)
            
            # Ensure burst time is at least 1
            burst_time = max(1, burst_time)
            
            process = Process(arrival_time, i)
            process.burst_time = burst_time
            process.remaining_time = burst_time
            process.priority = priority
            
            processes.append(process)
        
        # Sort by arrival time
        processes.sort(key=lambda p: p.arrival_time)
        return processes
        
    def run_simulation(self, num_processes, arrival_min, arrival_max, 
                      burst_min, burst_max, priority_min, priority_max, quantum):
        # Generate processes
        self.processes = self.generate_processes(num_processes, arrival_min, arrival_max, 
                                                 burst_min, burst_max, priority_min, priority_max)
        
        # Run selected algorithm
        algorithm = self.algorithm_var.get()
        
        if algorithm == "fcfs":
            self.simulate_fcfs()
        elif algorithm == "sjf":
            self.simulate_sjf()
        elif algorithm == "srtf":
            self.simulate_srtf()
        elif algorithm == "rr":
            self.simulate_round_robin(quantum)
        elif algorithm == "priority":
            self.simulate_priority(preemptive=False)
        elif algorithm == "priority_preemptive":
            self.simulate_priority(preemptive=True)
            
        # Add a delay to ensure simulation is visible before showing results
        time.sleep(2)  # Increased delay to allow animation to render
        
        # Generate final results
        self.root.after(0, self.show_results)
        
    def simulate_fcfs(self):
        """First Come First Serve - Non-preemptive"""
        ready_queue = deque()
        current_time = 0
        process_index = 0
        
        while len(self.completed_processes) < len(self.processes):
            if not self.simulation_running:
                break
            
            # Add newly arrived processes to ready queue
            while process_index < len(self.processes) and self.processes[process_index].arrival_time <= current_time:
                p = self.processes[process_index]
                p.state = "READY"
                ready_queue.append(p)
                process_index += 1
            
            # Record metrics
            self.time_points.append(current_time)
            self.ready_queue_data.append(len(ready_queue))
            
            # Execute process if available
            if ready_queue:
                process = ready_queue.popleft()
                process.state = "RUNNING"
                
                if process.start_time is None:
                    process.start_time = current_time
                    process.response_time = current_time - process.arrival_time
                
                # Record Gantt chart data
                self.gantt_data.append((current_time, process.process_id, process.burst_time))
                
                # Execute for full burst time (non-preemptive)
                current_time += process.burst_time
                
                # Process completed
                process.state = "TERMINATED"
                process.completion_time = current_time
                process.turnaround_time = current_time - process.arrival_time
                process.waiting_time = process.turnaround_time - process.burst_time
                
                self.completed_processes.append(process)
                
                self.status_var.set(f"Time: {current_time}ms | Completed: {len(self.completed_processes)}/{len(self.processes)}")
            else:
                # CPU idle
                current_time += 1
            
            # Force plot update every few iterations
            if current_time % 5 == 0:
                self.root.after(0, lambda: self.update_plots(0))
            
            time.sleep(0.1)  # Increased visualization delay for better visibility
    
    def simulate_sjf(self):
        """Shortest Job First - Non-preemptive"""
        ready_queue = []
        current_time = 0
        process_index = 0
        
        while len(self.completed_processes) < len(self.processes):
            if not self.simulation_running:
                break
            
            # Add newly arrived processes
            while process_index < len(self.processes) and self.processes[process_index].arrival_time <= current_time:
                p = self.processes[process_index]
                p.state = "READY"
                ready_queue.append(p)
                process_index += 1
            
            # Record metrics
            self.time_points.append(current_time)
            self.ready_queue_data.append(len(ready_queue))
            
            if ready_queue:
                # Sort by burst time (shortest first)
                ready_queue.sort(key=lambda p: p.burst_time)
                process = ready_queue.pop(0)
                process.state = "RUNNING"
                
                if process.start_time is None:
                    process.start_time = current_time
                    process.response_time = current_time - process.arrival_time
                
                self.gantt_data.append((current_time, process.process_id, process.burst_time))
                current_time += process.burst_time
                
                process.state = "TERMINATED"
                process.completion_time = current_time
                process.turnaround_time = current_time - process.arrival_time
                process.waiting_time = process.turnaround_time - process.burst_time
                
                self.completed_processes.append(process)
                self.status_var.set(f"Time: {current_time}ms | Completed: {len(self.completed_processes)}/{len(self.processes)}")
            else:
                current_time += 1
            
            # Force plot update every few iterations
            if current_time % 5 == 0:
                self.root.after(0, lambda: self.update_plots(0))
            
            time.sleep(0.1)  # Increased visualization delay
    
    def simulate_srtf(self):
        """Shortest Remaining Time First - Preemptive"""
        ready_queue = []
        current_time = 0
        process_index = 0
        current_process = None
        
        while len(self.completed_processes) < len(self.processes) or current_process:
            if not self.simulation_running:
                break
            
            # Add newly arrived processes
            while process_index < len(self.processes) and self.processes[process_index].arrival_time <= current_time:
                p = self.processes[process_index]
                p.state = "READY"
                ready_queue.append(p)
                process_index += 1
            
            # Add current process back to queue for comparison (only if it exists and has remaining time)
            if current_process and current_process.remaining_time > 0:
                current_process.state = "READY"
                ready_queue.append(current_process)
            
            # Record metrics
            self.time_points.append(current_time)
            self.ready_queue_data.append(len(ready_queue))
            
            if ready_queue:
                # Sort by remaining time
                ready_queue.sort(key=lambda p: p.remaining_time)
                process = ready_queue.pop(0)
                
                # Only update state if it's a different process
                if process != current_process:
                    if current_process:
                        current_process.state = "READY"
                    process.state = "RUNNING"
                    current_process = process
                    
                    if process.start_time is None:
                        process.start_time = current_time
                        process.response_time = current_time - process.arrival_time
                
                # Execute for 1 time unit
                self.gantt_data.append((current_time, process.process_id, 1))
                process.remaining_time -= 1
                current_time += 1
                
                if process.remaining_time == 0:
                    process.state = "TERMINATED"
                    process.completion_time = current_time
                    process.turnaround_time = current_time - process.arrival_time
                    process.waiting_time = process.turnaround_time - process.burst_time
                    self.completed_processes.append(process)
                    current_process = None
                    self.status_var.set(f"Time: {current_time}ms | Completed: {len(self.completed_processes)}/{len(self.processes)}")
            else:
                current_time += 1
                current_process = None
            
            # Force plot update every few iterations
            if current_time % 3 == 0:
                self.root.after(0, lambda: self.update_plots(0))
            
            time.sleep(0.05)  # Increased delay for SRTF visualization
    
    def simulate_round_robin(self, quantum):
        """Round Robin - Preemptive with time quantum"""
        ready_queue = deque()
        current_time = 0
        process_index = 0
        
        while len(self.completed_processes) < len(self.processes):
            if not self.simulation_running:
                break
            
            # Add newly arrived processes
            while process_index < len(self.processes) and self.processes[process_index].arrival_time <= current_time:
                p = self.processes[process_index]
                p.state = "READY"
                ready_queue.append(p)
                process_index += 1
            
            # Record metrics
            self.time_points.append(current_time)
            self.ready_queue_data.append(len(ready_queue))
            
            if ready_queue:
                process = ready_queue.popleft()
                
                if process.start_time is None:
                    process.start_time = current_time
                    process.response_time = current_time - process.arrival_time
                
                process.state = "RUNNING"
                
                # Execute for quantum or remaining time, whichever is smaller
                exec_time = min(quantum, process.remaining_time)
                self.gantt_data.append((current_time, process.process_id, exec_time))
                
                process.remaining_time -= exec_time
                current_time += exec_time
                
                # Check for new arrivals during execution
                while process_index < len(self.processes) and self.processes[process_index].arrival_time <= current_time:
                    p = self.processes[process_index]
                    p.state = "READY"
                    ready_queue.append(p)
                    process_index += 1
                
                if process.remaining_time == 0:
                    process.state = "TERMINATED"
                    process.completion_time = current_time
                    process.turnaround_time = current_time - process.arrival_time
                    process.waiting_time = process.turnaround_time - process.burst_time
                    self.completed_processes.append(process)
                    self.status_var.set(f"Time: {current_time}ms | Completed: {len(self.completed_processes)}/{len(self.processes)}")
                else:
                    # Re-add to queue
                    process.state = "READY"
                    ready_queue.append(process)
            else:
                current_time += 1
            
            # Force plot update every few iterations
            if current_time % 5 == 0:
                self.root.after(0, lambda: self.update_plots(0))
            
            time.sleep(0.1)  # Increased visualization delay
    
    def simulate_priority(self, preemptive=False):
        """Priority Scheduling (lower priority number = higher priority)"""
        ready_queue = []
        current_time = 0
        process_index = 0
        current_process = None
        
        while len(self.completed_processes) < len(self.processes) or (preemptive and current_process):
            if not self.simulation_running:
                break
            
            # Add newly arrived processes
            while process_index < len(self.processes) and self.processes[process_index].arrival_time <= current_time:
                p = self.processes[process_index]
                p.state = "READY"
                ready_queue.append(p)
                process_index += 1
            
            if preemptive and current_process:
                ready_queue.append(current_process)
            
            # Record metrics
            self.time_points.append(current_time)
            self.ready_queue_data.append(len(ready_queue))
            
            if ready_queue:
                # Sort by priority (lower number = higher priority)
                ready_queue.sort(key=lambda p: p.priority)
                process = ready_queue.pop(0)
                
                if process.start_time is None:
                    process.start_time = current_time
                    process.response_time = current_time - process.arrival_time
                
                process.state = "RUNNING"
                
                if preemptive:
                    # Execute for 1 time unit
                    exec_time = 1
                    self.gantt_data.append((current_time, process.process_id, exec_time))
                    process.remaining_time -= 1
                    current_time += 1
                    
                    if process.remaining_time == 0:
                        process.state = "TERMINATED"
                        process.completion_time = current_time
                        process.turnaround_time = current_time - process.arrival_time
                        process.waiting_time = process.turnaround_time - process.burst_time
                        self.completed_processes.append(process)
                        current_process = None
                        self.status_var.set(f"Time: {current_time}ms | Completed: {len(self.completed_processes)}/{len(self.processes)}")
                    else:
                        current_process = process
                else:
                    # Non-preemptive: execute till completion
                    self.gantt_data.append((current_time, process.process_id, process.burst_time))
                    current_time += process.burst_time
                    
                    process.state = "TERMINATED"
                    process.completion_time = current_time
                    process.turnaround_time = current_time - process.arrival_time
                    process.waiting_time = process.turnaround_time - process.burst_time
                    self.completed_processes.append(process)
                    self.status_var.set(f"Time: {current_time}ms | Completed: {len(self.completed_processes)}/{len(self.processes)}")
            else:
                current_time += 1
                if preemptive:
                    current_process = None
            
            # Force plot update every few iterations
            if current_time % 5 == 0:
                self.root.after(0, lambda: self.update_plots(0))
            
            time.sleep(0.05 if preemptive else 0.1)  # Increased delays for better visualization
    
    def update_plots(self, frame):
        try:
            if not self.time_points:
                return
            
            # Check if the window still exists
            if not self.root.winfo_exists():
                return
            
            # Update ready queue plot
            self.ax_ready_queue.clear()
            self.ax_ready_queue.plot(self.time_points, self.ready_queue_data, color='#3498db', linewidth=3)
            self.ax_ready_queue.fill_between(self.time_points, self.ready_queue_data, alpha=0.3, color='#3498db')
            self.ax_ready_queue.set_title('Ready Queue Length Over Time', fontsize=12, fontweight='bold', color='#2c3e50')
            self.ax_ready_queue.set_xlabel('Time (ms)', fontsize=10, color='#34495e')
            self.ax_ready_queue.set_ylabel('Processes in Ready Queue', fontsize=10, color='#34495e')
            self.ax_ready_queue.grid(True, alpha=0.3, color='#bdc3c7')
            self.ax_ready_queue.set_facecolor('#ffffff')
            
            # Update timeline plot
            self.ax_timeline.clear()
            if self.completed_processes:
                completion_times = [p.completion_time for p in self.completed_processes]
                self.ax_timeline.step(completion_times, range(1, len(completion_times) + 1), 
                                     color='#27ae60', linewidth=3, where='post')
            
            self.ax_timeline.set_title('Process Execution Timeline', fontsize=12, fontweight='bold', color='#2c3e50')
            self.ax_timeline.set_xlabel('Time (ms)', fontsize=10, color='#34495e')
            self.ax_timeline.set_ylabel('Cumulative Processes Completed', fontsize=10, color='#34495e')
            self.ax_timeline.grid(True, alpha=0.3, color='#bdc3c7')
            self.ax_timeline.set_facecolor('#ffffff')
            
            self.canvas_live.draw()
        except Exception as e:
            # Silently handle any drawing errors
            pass
    
    def show_results(self):
        if not self.completed_processes:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "No processes completed.")
            return
        
        # Calculate metrics
        throughput = len(self.completed_processes)
        avg_waiting_time = statistics.mean([p.waiting_time for p in self.completed_processes])
        avg_turnaround_time = statistics.mean([p.turnaround_time for p in self.completed_processes])
        avg_response_time = statistics.mean([p.response_time for p in self.completed_processes if p.response_time is not None])
        
        total_time = max([p.completion_time for p in self.completed_processes])
        total_burst = sum([p.burst_time for p in self.completed_processes])
        cpu_utilization = (total_burst / total_time) * 100 if total_time > 0 else 0
        cpu_utilization = min(cpu_utilization, 100)  # Cap at 100%
        
        # Display results
        algo_names = {
            "fcfs": "First Come First Serve (FCFS)",
            "sjf": "Shortest Job First (SJF)",
            "srtf": "Shortest Remaining Time First (SRTF)",
            "rr": "Round Robin (RR)",
            "priority": "Priority Scheduling (Non-Preemptive)",
            "priority_preemptive": "Priority Scheduling (Preemptive)"
        }
        
        algo_name = algo_names.get(self.algorithm_var.get(), "Unknown")
        
        results_text = f"""
⚙️ PROCESS SCHEDULING RESULTS
{'='*60}
Algorithm: {algo_name}
Total Processes: {len(self.processes)}

📊 PERFORMANCE METRICS:
• Throughput: {throughput} processes completed
• Average Waiting Time: {avg_waiting_time:.2f} ms
• Average Turnaround Time: {avg_turnaround_time:.2f} ms
• Average Response Time: {avg_response_time:.2f} ms

⚡ CPU METRICS:
• Total Execution Time: {total_time} ms
• CPU Utilization: {cpu_utilization:.1f}%
• Context Switches: {len(self.gantt_data)}

📋 PROCESS DETAILS:
"""
        
        # Add individual process details
        for p in self.completed_processes[:10]:  # Show first 10
            results_text += f"  P{p.process_id}: Arrival={p.arrival_time}ms, Burst={p.burst_time}ms, "
            results_text += f"Wait={p.waiting_time}ms, TAT={p.turnaround_time}ms, Priority={p.priority}\n"
        
        if len(self.completed_processes) > 10:
            results_text += f"  ... and {len(self.completed_processes) - 10} more processes\n"
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, results_text)
        
        # Update results plots
        self.plot_results_charts()
        
        # Update Gantt chart
        self.plot_gantt_chart()
        
        # Keep animation running to show final results
        # Animation will be stopped when user starts new simulation or closes window
        
        # Force update the live plots to show final data
        self.update_plots(0)
        
        # Trigger memory OS analysis
        self.analyze_memory_os()
        
        self.simulation_running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_var.set("Simulation completed!")
    
    def plot_results_charts(self):
        """Plot performance analysis charts"""
        # Clear all result plots
        for ax in [self.ax_throughput, self.ax_waiting, self.ax_turnaround, self.ax_response]:
            ax.clear()
        
        # Throughput chart
        self.ax_throughput.bar(['Processes\nCompleted'], [len(self.completed_processes)], 
                              color='skyblue', alpha=0.7, edgecolor='navy', linewidth=2)
        self.ax_throughput.set_title('Throughput', fontweight='bold')
        self.ax_throughput.set_ylabel('Count')
        
        # Waiting time distribution
        waiting_times = [p.waiting_time for p in self.completed_processes]
        self.ax_waiting.hist(waiting_times, bins=min(20, len(self.completed_processes)), 
                            color='orange', alpha=0.7, edgecolor='darkorange')
        avg_wait = statistics.mean(waiting_times)
        self.ax_waiting.axvline(avg_wait, color='red', linestyle='--', linewidth=2,
                               label=f'Avg: {avg_wait:.1f}ms')
        self.ax_waiting.set_title('Waiting Time Distribution', fontweight='bold')
        self.ax_waiting.set_xlabel('Time (ms)')
        self.ax_waiting.set_ylabel('Frequency')
        self.ax_waiting.legend()
        
        # Turnaround time distribution
        turnaround_times = [p.turnaround_time for p in self.completed_processes]
        self.ax_turnaround.hist(turnaround_times, bins=min(20, len(self.completed_processes)), 
                               color='green', alpha=0.7, edgecolor='darkgreen')
        avg_tat = statistics.mean(turnaround_times)
        self.ax_turnaround.axvline(avg_tat, color='red', linestyle='--', linewidth=2,
                                  label=f'Avg: {avg_tat:.1f}ms')
        self.ax_turnaround.set_title('Turnaround Time Distribution', fontweight='bold')
        self.ax_turnaround.set_xlabel('Time (ms)')
        self.ax_turnaround.set_ylabel('Frequency')
        self.ax_turnaround.legend()
        
        # Response time chart
        response_times = [p.response_time for p in self.completed_processes if p.response_time is not None]
        if response_times:
            self.ax_response.hist(response_times, bins=min(20, len(response_times)), 
                                 color='purple', alpha=0.7, edgecolor='indigo')
            avg_resp = statistics.mean(response_times)
            self.ax_response.axvline(avg_resp, color='red', linestyle='--', linewidth=2,
                                    label=f'Avg: {avg_resp:.1f}ms')
            self.ax_response.set_title('Response Time Distribution', fontweight='bold')
            self.ax_response.set_xlabel('Time (ms)')
            self.ax_response.set_ylabel('Frequency')
            self.ax_response.legend()
        
        self.fig_results.tight_layout()
        self.canvas_results.draw()
    
    def plot_gantt_chart(self):
        """Create Gantt chart showing process execution timeline"""
        self.ax_gantt.clear()
        
        if not self.gantt_data:
            return
        
        # Consolidate consecutive executions of same process
        consolidated = []
        if self.gantt_data:
            current_start = self.gantt_data[0][0]
            current_pid = self.gantt_data[0][1]
            current_duration = self.gantt_data[0][2]
            
            for i in range(1, len(self.gantt_data)):
                start, pid, duration = self.gantt_data[i]
                
                if pid == current_pid and start == current_start + current_duration:
                    # Same process, consecutive execution
                    current_duration += duration
                else:
                    # Different process or gap, save current and start new
                    consolidated.append((current_start, current_pid, current_duration))
                    current_start = start
                    current_pid = pid
                    current_duration = duration
            
            # Add last segment
            consolidated.append((current_start, current_pid, current_duration))
        
        # Plot Gantt chart
        colors = plt.cm.tab20(np.linspace(0, 1, len(self.processes)))
        process_colors = {p.process_id: colors[i % len(colors)] for i, p in enumerate(self.processes)}
        
        y_pos = 0
        for start, pid, duration in consolidated:
            self.ax_gantt.barh(y_pos, duration, left=start, height=0.8, 
                              color=process_colors[pid], edgecolor='black', linewidth=0.5)
            # Add process label
            self.ax_gantt.text(start + duration/2, y_pos, f'P{pid}', 
                              ha='center', va='center', fontweight='bold', fontsize=8)
        
        self.ax_gantt.set_xlabel('Time (ms)', fontweight='bold')
        self.ax_gantt.set_ylabel('CPU', fontweight='bold')
        self.ax_gantt.set_title('Process Execution Gantt Chart', fontweight='bold', fontsize=12)
        self.ax_gantt.set_yticks([y_pos])
        self.ax_gantt.set_yticklabels(['CPU'])
        self.ax_gantt.grid(True, axis='x', alpha=0.3)
        
        # Add legend
        legend_elements = [plt.Rectangle((0,0),1,1, facecolor=process_colors[p.process_id], 
                                        edgecolor='black', label=f'P{p.process_id}')
                          for p in self.processes[:10]]  # Show first 10 in legend
        if len(self.processes) > 10:
            self.ax_gantt.legend(handles=legend_elements, loc='upper right', 
                                bbox_to_anchor=(1.15, 1), ncol=2, fontsize=8)
        else:
            self.ax_gantt.legend(handles=legend_elements, loc='upper right', 
                                bbox_to_anchor=(1.12, 1), fontsize=8)
        
        self.fig_gantt.tight_layout()
        self.canvas_gantt.draw()
    
    def setup_memory_analysis(self, parent):
        """Setup Memory OS Analysis visualization"""
        # Memory analysis button
        analyze_btn = ttk.Button(parent, text="Analyze Memory OS Performance", 
                               command=self.analyze_memory_os, style='Success.TButton')
        analyze_btn.pack(pady=15, ipadx=10, ipady=5)
        
        # Memory analysis text area
        self.memory_text = tk.Text(parent, height=15, font=('Consolas', 9), 
                                  bg='#ffffff', fg='#2c3e50', relief='solid', borderwidth=1)
        self.memory_text.pack(fill='both', expand=True, padx=15, pady=10)
        
        # Memory comparison frame
        self.memory_comparison_frame = ttk.LabelFrame(parent, text="Memory OS Comparison", padding=15)
        self.memory_comparison_frame.pack(fill='x', padx=15, pady=10)
        self.memory_comparison_frame.configure(style='Card.TLabelframe')
        
    def analyze_memory_os(self):
        """Analyze memory usage patterns and OS-level performance"""
        if not self.completed_processes:
            self.memory_text.delete(1.0, tk.END)
            self.memory_text.insert(tk.END, "No completed processes to analyze.")
            return
        
        # Calculate memory-related metrics
        total_memory_usage = sum(p.burst_time for p in self.completed_processes)
        avg_memory_per_process = total_memory_usage / len(self.completed_processes)
        
        # Simulate memory fragmentation
        memory_fragments = self.simulate_memory_fragmentation()
        
        # Calculate memory efficiency
        memory_efficiency = self.calculate_memory_efficiency()
        
        # Simulate page faults and cache hits
        page_faults = self.simulate_page_faults()
        cache_hits = self.simulate_cache_performance()
        
        # Generate analysis report
        analysis_report = f"""
💾 MEMORY OS ANALYSIS REPORT
{'='*60}

📊 MEMORY USAGE STATISTICS:
• Total Memory Usage: {total_memory_usage} ms
• Average Memory per Process: {avg_memory_per_process:.2f} ms
• Memory Fragmentation Level: {memory_fragments:.1f}%
• Memory Efficiency: {memory_efficiency:.1f}%

🔄 OS-LEVEL PERFORMANCE:
• Page Faults: {page_faults}
• Cache Hit Rate: {cache_hits:.1f}%
• Context Switches: {len(self.gantt_data)}
• Memory Allocation Efficiency: {self.calculate_allocation_efficiency():.1f}%

📈 ALGORITHM-SPECIFIC MEMORY IMPACT:
• Memory Fragmentation by Algorithm: {self.get_algorithm_memory_impact()}
• Process Memory Footprint: {self.calculate_process_memory_footprint()}

🔍 DETAILED MEMORY ANALYSIS:
"""
        
        # Add process-specific memory analysis
        for i, process in enumerate(self.completed_processes[:5]):
            memory_footprint = process.burst_time * 0.1  # Simulate memory footprint
            analysis_report += f"  P{process.process_id}: Memory={memory_footprint:.1f}MB, "
            analysis_report += f"Fragmentation={random.uniform(5, 25):.1f}%, "
            analysis_report += f"Cache_Efficiency={random.uniform(70, 95):.1f}%\n"
        
        if len(self.completed_processes) > 5:
            analysis_report += f"  ... and {len(self.completed_processes) - 5} more processes\n"
        
        self.memory_text.delete(1.0, tk.END)
        self.memory_text.insert(tk.END, analysis_report)
        
        # Update memory comparison
        self.update_memory_comparison()
    
    def simulate_memory_fragmentation(self):
        """Simulate memory fragmentation based on scheduling algorithm"""
        algorithm = self.algorithm_var.get()
        
        # Different algorithms have different fragmentation patterns
        fragmentation_map = {
            "fcfs": random.uniform(15, 25),
            "sjf": random.uniform(10, 20),
            "srtf": random.uniform(20, 35),
            "rr": random.uniform(25, 40),
            "priority": random.uniform(18, 30),
            "priority_preemptive": random.uniform(22, 35)
        }
        
        return fragmentation_map.get(algorithm, 20.0)
    
    def calculate_memory_efficiency(self):
        """Calculate memory efficiency based on process execution patterns"""
        if not self.completed_processes:
            return 0
        
        total_time = max(p.completion_time for p in self.completed_processes)
        total_burst = sum(p.burst_time for p in self.completed_processes)
        
        # Memory efficiency = (useful work / total time) * 100
        efficiency = (total_burst / total_time) * 100 if total_time > 0 else 0
        return min(efficiency, 100)  # Cap at 100%
    
    def simulate_page_faults(self):
        """Simulate page faults based on process characteristics"""
        total_faults = 0
        for process in self.completed_processes:
            # Larger processes and longer execution times lead to more page faults
            base_faults = process.burst_time // 10
            priority_factor = (6 - process.priority) * 2  # Higher priority = more faults
            total_faults += base_faults + priority_factor
        
        return max(0, int(total_faults))
    
    def simulate_cache_performance(self):
        """Simulate cache hit rate based on scheduling patterns"""
        algorithm = self.algorithm_var.get()
        
        # Different algorithms have different cache performance
        cache_rates = {
            "fcfs": random.uniform(75, 85),
            "sjf": random.uniform(80, 90),
            "srtf": random.uniform(70, 80),
            "rr": random.uniform(65, 75),
            "priority": random.uniform(78, 88),
            "priority_preemptive": random.uniform(72, 82)
        }
        
        return cache_rates.get(algorithm, 80.0)
    
    def calculate_allocation_efficiency(self):
        """Calculate memory allocation efficiency"""
        if not self.completed_processes:
            return 0
        
        # Simulate allocation efficiency based on process sizes and timing
        total_efficiency = 0
        for process in self.completed_processes:
            # Smaller processes and better timing = higher efficiency
            size_factor = max(0, 100 - process.burst_time)
            timing_factor = max(0, 100 - (process.waiting_time * 2))
            efficiency = (size_factor + timing_factor) / 2
            total_efficiency += efficiency
        
        return total_efficiency / len(self.completed_processes)
    
    def get_algorithm_memory_impact(self):
        """Get memory impact analysis for current algorithm"""
        algorithm = self.algorithm_var.get()
        
        impacts = {
            "fcfs": "Low fragmentation, predictable memory usage",
            "sjf": "Optimal memory utilization, minimal fragmentation",
            "srtf": "High fragmentation due to frequent preemption",
            "rr": "Moderate fragmentation, fair memory distribution",
            "priority": "Priority-based memory allocation",
            "priority_preemptive": "High fragmentation, priority-driven allocation"
        }
        
        return impacts.get(algorithm, "Unknown impact")
    
    def calculate_process_memory_footprint(self):
        """Calculate average memory footprint per process"""
        if not self.completed_processes:
            return "0 MB"
        
        total_footprint = sum(p.burst_time * 0.1 for p in self.completed_processes)
        avg_footprint = total_footprint / len(self.completed_processes)
        return f"{avg_footprint:.1f} MB"
    
    def update_memory_comparison(self):
        """Update memory comparison display"""
        # Clear existing widgets
        for widget in self.memory_comparison_frame.winfo_children():
            widget.destroy()
        
        if not self.completed_processes:
            ttk.Label(self.memory_comparison_frame, 
                     text="No data available for comparison").pack()
            return
        
        # Create comparison metrics
        metrics = [
            ("Memory Efficiency", f"{self.calculate_memory_efficiency():.1f}%"),
            ("Fragmentation", f"{self.simulate_memory_fragmentation():.1f}%"),
            ("Cache Hit Rate", f"{self.simulate_cache_performance():.1f}%"),
            ("Page Faults", str(self.simulate_page_faults())),
            ("Allocation Efficiency", f"{self.calculate_allocation_efficiency():.1f}%")
        ]
        
        for i, (metric, value) in enumerate(metrics):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(self.memory_comparison_frame, text=f"{metric}:").grid(
                row=row, column=col, sticky='w', padx=5, pady=2)
            ttk.Label(self.memory_comparison_frame, text=value, 
                    font=('Arial', 9, 'bold')).grid(
                row=row, column=col+1, sticky='w', padx=5, pady=2)

if __name__ == "__main__":
    root = tk.Tk()
    app = ProcessSchedulerGUI(root)
    root.mainloop()