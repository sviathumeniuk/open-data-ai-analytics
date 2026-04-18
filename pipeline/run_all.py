import sys
from loader import load
from quality import analyze_quality
from research import run_research
from visualization import visualize

def main():
    try:
        load()
        analyze_quality()
        run_research()
        visualize()
        print("Pipeline finished successfully!")
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

