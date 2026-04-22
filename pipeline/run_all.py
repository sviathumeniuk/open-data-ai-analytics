import sys
from pipeline.loader import load
from pipeline.quality import analyze_quality
from pipeline.research import run_research
from pipeline.visualization import visualize

def main():
    try:
        load()
        analyze_quality()
        run_research()
        visualize()
        print("--- Pipeline Finished ---")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
