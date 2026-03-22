from app.agent.loop import run_agent

# A simple HTML page to convert — we'll use something real later
SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>My Business Site</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; }
        header { background: #333; color: white; padding: 20px; }
        nav a { color: white; margin: 0 10px; text-decoration: none; }
        main { max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
        .hero { text-align: center; padding: 80px 20px; background: #f5f5f5; }
        footer { background: #333; color: white; text-align: center; padding: 20px; }
    </style>
</head>
<body>
    <header>
        <nav>
            <a href="#">Home</a>
            <a href="#">About</a>
            <a href="#">Services</a>
            <a href="#">Contact</a>
        </nav>
    </header>
    <main>
        <section class="hero">
            <h1>Welcome to My Business</h1>
            <p>We provide excellent services to our clients.</p>
        </section>
        <section>
            <h2>Our Services</h2>
            <p>Lorem ipsum dolor sit amet.</p>
        </section>
    </main>
    <footer>
        <p>Copyright 2024 My Business</p>
    </footer>
</body>
</html>
"""

if __name__ == "__main__":
    result = run_agent(SAMPLE_HTML, theme_name="my-business-theme")
    print("\nFinal workspace contents:")
    for f in result["files"]:
        print(f"  {f}")
