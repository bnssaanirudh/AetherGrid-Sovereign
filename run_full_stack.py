import subprocess
import time
import sys
import os

def run_process(name, cmd, cwd, env=None):
    print(f"Starting {name}...")
    # using shell=True allows npm/uvicorn to be found easily on windows
    return subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        shell=True,
        stdout=sys.stdout,
        stderr=sys.stderr
    )

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct PYTHONPATH for internal packages
    packages_dir = os.path.join(root_dir, "packages")
    python_paths = [os.path.join(root_dir, "backend"), root_dir]
    if os.path.exists(packages_dir):
        for pkg in os.listdir(packages_dir):
            pkg_root = os.path.join(packages_dir, pkg)
            python_paths.append(pkg_root)
            pkg_src = os.path.join(pkg_root, "src")
            if os.path.isdir(pkg_src):
                python_paths.append(pkg_src)
    
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(python_paths) + (os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")
    env["OPENWEATHER_API_KEY"] = os.environ.get("OPENWEATHER_API_KEY", "dummy_key")
    env["SECRET_KEY"] = "473fd6bbc159a46be1b606286a567360e2a4e3e24ce7a70f8ee2cbd6bf984ef4"
    env["API_KEYS"] = "59b192eca07275bb01c546ee33eca182,b8f9704066e579dda85c07d45eadf06a"
    
    # 1. Start Backend (uvicorn) on port 8080
    backend_proc = run_process(
        "FastAPI Backend", 
        "python -m uvicorn app.main:app --host 0.0.0.0 --port 8080",
        cwd=os.path.join(root_dir, "backend"),
        env=env
    )
    
    # Wait a moment for backend to initialize
    time.sleep(2)
    
    # 2. Start Unified Next.js Website on port 3000
    website_proc = run_process(
        "Unified Next.js Web App",
        "npm run dev",
        cwd=os.path.join(root_dir, "website")
    )
    
    print("\n" + "="*50)
    print("AETHERGRID SOVEREIGN IS LIVE")
    print("="*50)
    print("Backend API:       http://localhost:8080")
    print("Backend Docs:      http://localhost:8080/docs")
    print("Web Application:   http://localhost:3000")
    print("Press Ctrl+C to terminate all services.")
    print("="*50 + "\n")
    
    try:
        # Keep main thread alive
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down all services...")
        backend_proc.terminate()
        website_proc.terminate()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
