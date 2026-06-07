import os
import uuid
from playwright.sync_api import sync_playwright

def record():
    # Use a unique email to ensure account creation works every time
    unique_email = f"demo_{uuid.uuid4().hex[:6]}@example.com"
    
    with open("sample_demo_data.csv", "w") as f:
        f.write("department,expenses,revenue\nSales,5000,12000\nMarketing,3000,6000\nEngineering,15000,2000\nHR,1000,500\n")

    os.makedirs("videos", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="videos/",
            record_video_size={"width": 1920, "height": 1080},
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        page.on("dialog", lambda dialog: dialog.accept())

        print("1. Loading Web App...")
        page.goto("http://localhost:3000/login")
        
        print(f"2. Authenticating User ({unique_email})...")
        page.fill("input[type='email']", unique_email)
        page.fill("input[type='password']", "password123")
        page.click("button:has-text('Sign Up')")
        page.wait_for_timeout(1000)
        page.click("button:has-text('Create Account')")
        
        page.wait_for_url("**/dashboard", timeout=15000)
        
        print("3. Uploading Dataset...")
        page.set_input_files("input[type='file']", "sample_demo_data.csv")
        page.wait_for_timeout(1000)
        page.click("button:has-text('Ingest')")
        page.wait_for_timeout(3000)
        
        print("4. Navigating to Dataset Library...")
        page.goto("http://localhost:3000/dashboard/datasets")
        page.wait_for_timeout(2000)
        
        print("5. Previewing Dataset...")
        # Click the view button to open dialog
        page.click("button:has-text('View')")
        page.wait_for_timeout(4000)
        page.keyboard.press("Escape")
        page.wait_for_timeout(1000)

        print("6. Navigating to AI Chat Workspace...")
        page.goto("http://localhost:3000/dashboard/chat")
        page.wait_for_timeout(2000)
        
        page.check("input[type='checkbox']")
        
        print("7. Asking AI to analyze and generate a plot...")
        # Complex query with keywords to force the LangChain anomaly detection router
        complex_query = "Run a deep statistical exploration to investigate anomalies in the dataset. Use custom algorithmic reasoning to detect outliers, and generate an interactive Plotly scatter chart of the results."
        page.fill("input[placeholder*='Ask your data']", complex_query)
        page.wait_for_timeout(1000)
        page.click("button[type='submit']")
        
        print("8. Waiting for AI reasoning loop to finish...")
        try:
            # 120s timeout to give LangChain plenty of time to write and execute python code
            page.wait_for_selector(".js-plotly-plot", timeout=120000)
            print("Chart generated! Capturing final seconds...")
            page.wait_for_timeout(4000)
        except Exception as e:
            print("Wait for chart failed:", e)
        
        context.close()
        browser.close()
        
        # Print the latest file
        files = sorted(os.listdir("videos"), key=lambda x: os.path.getmtime(os.path.join("videos", x)), reverse=True)
        if files:
            print(f"Video recorded successfully! Saved to: videos/{files[0]}")
        else:
            print("Video failed to save.")

if __name__ == "__main__":
    record()
