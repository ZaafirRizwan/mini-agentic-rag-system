import sys
import os

# Add current directory to sys.path
sys.path.append(os.getcwd())

from src.agent_graph import app

def generate_graph_image():
    print("Generating graph visualization...")
    try:
        # Get the graph object
        graph = app.get_graph()
        
        # Generate Mermaid PNG
        png_data = graph.draw_mermaid_png()
        
        output_path = "agent_graph.png"
        with open(output_path, "wb") as f:
            f.write(png_data)
            
        print(f"✅ Graph visualization saved to {output_path}")
        
    except Exception as e:
        print(f"❌ Failed to generate PNG: {e}")
        print("Attempting to print Mermaid syntax instead...")
        try:
            print("\nMermaid Syntax:")
            print(app.get_graph().draw_mermaid())
        except Exception as e2:
            print(f"❌ Failed to generate Mermaid syntax: {e2}")

if __name__ == "__main__":
    generate_graph_image()
