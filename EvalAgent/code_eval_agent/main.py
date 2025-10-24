#!/usr/bin/env python3
"""
Local Code Agent Main Program
Local code agent system based on Google ADK
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from examples.code_agent_local.agent import local_code_agent_system
from examples.code_agent_local.config import WORKSPACE_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class LocalCodeAgentCLI:
    """Local Code Agent Command Line Interface"""
    
    def __init__(self):
        self.agent_system = local_code_agent_system
        self.root_agent = self.agent_system.get_root_agent()
    
    async def run_interactive(self):
        """Run interactive mode"""
        print("=" * 60)
        print("🤖 Local Code Agent System")
        print("=" * 60)
        print("Supported features:")
        print("1. Complete code development (planning, writing, testing, debugging, summary)")
        print("2. Quick code execution (mathematical calculations, data processing)")
        print("3. File management (create, read, modify, delete)")
        print("4. Workspace management")
        print("=" * 60)
        print("Enter 'quit' or 'exit' to exit")
        print("Enter 'help' to view help")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\n💬 Please enter your request: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if user_input.lower() == 'help':
                    self.show_help()
                    continue
                
                if not user_input:
                    continue
                
                print(f"\n🔄 Processing: {user_input}")
                
                # Run agent
                result = await self.run_agent(user_input)
                
                print(f"\n✅ Processing completed:")
                print(f"Status: {result.get('status', 'unknown')}")
                if 'response' in result:
                    print(f"Response: {result['response']}")
                if 'error' in result:
                    print(f"Error: {result['error']}")
                
            except KeyboardInterrupt:
                print("\n\n👋 User interrupted, goodbye!")
                break
            except Exception as e:
                logger.error(f"Runtime error: {e}")
                print(f"❌ Error occurred: {e}")
    
    async def run_single_task(self, task: str):
        """Run single task"""
        print(f"🔄 Processing task: {task}")
        
        result = await self.run_agent(task)
        
        print(f"\n✅ Task completed:")
        print(f"Status: {result.get('status', 'unknown')}")
        if 'response' in result:
            print(f"Response: {result['response']}")
        if 'error' in result:
            print(f"Error: {result['error']}")
        
        return result
    
    async def run_agent(self, user_input: str) -> Dict[str, Any]:
        """Run agent system"""
        try:
            # Here should call actual agent running logic
            # Currently returning mock result
            result = {
                "status": "success",
                "user_input": user_input,
                "response": f"Local Code Agent has processed your request: {user_input}",
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # Simulate processing time
            await asyncio.sleep(1)
            
            return result
            
        except Exception as e:
            logger.error(f"Agent runtime error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "user_input": user_input
            }
    
    def show_help(self):
        """Show help information"""
        help_text = """
📖 Local Code Agent Help

🔧 Main Features:
1. Code Development - Create complete Python projects
2. Code Execution - Run Python code snippets
3. File Management - Manage files and directories
4. Workspace - Create workspace environment

💡 Usage Examples:

Code Development:
- "Create a calculator program"
- "Help me write a file processing tool"
- "Develop a simple web application"

Code Execution:
- "Calculate 2 + 2 * 3"
- "Generate a random number list"
- "Read CSV file and display first 5 rows"

File Management:
- "Create workspace"
- "List current files"
- "Read file content"

🔒 Security Features:
- Sandbox environment execution
- File operation restrictions
- System command whitelist

📁 Workspace: {workspace_dir}
        """.format(workspace_dir=WORKSPACE_DIR)
        
        print(help_text)
    
    def show_examples(self):
        """Show examples"""
        examples = [
            {
                "category": "Code Development",
                "examples": [
                    "Create a simple calculator program",
                    "Help me write a file batch rename tool",
                    "Develop a simple todo application"
                ]
            },
            {
                "category": "Code Execution",
                "examples": [
                    "Calculate the first 10 terms of Fibonacci sequence",
                    "Generate a list of 100 random numbers",
                    "Read and analyze CSV data"
                ]
            },
            {
                "category": "File Management",
                "examples": [
                    "Create a new workspace",
                    "List all files in current directory",
                    "Read and display file content"
                ]
            }
        ]
        
        print("\n📚 Usage Examples:")
        for category in examples:
            print(f"\n{category['category']}:")
            for example in category['examples']:
                print(f"  - {example}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Local Code Agent - Code agent system based on Google ADK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python main.py                    # Interactive mode
  python main.py -t "Calculate 2+2" # Execute single task
  python main.py --examples         # Show examples
  python main.py --help             # Show help
        """
    )
    
    parser.add_argument(
        '-t', '--task',
        type=str,
        help='Task to execute'
    )
    
    parser.add_argument(
        '--examples',
        action='store_true',
        help='Show usage examples'
    )
    
    parser.add_argument(
        '--workspace',
        type=str,
        default=WORKSPACE_DIR,
        help=f'Workspace directory (default: {WORKSPACE_DIR})'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output mode'
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create workspace directory
    workspace_path = Path(args.workspace)
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    # Create CLI instance
    cli = LocalCodeAgentCLI()
    
    async def run():
        if args.examples:
            cli.show_examples()
        elif args.task:
            await cli.run_single_task(args.task)
        else:
            await cli.run_interactive()
    
    # Run main program
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n👋 Program interrupted by user")
    except Exception as e:
        logger.error(f"Program runtime error: {e}")
        print(f"❌ Program error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


