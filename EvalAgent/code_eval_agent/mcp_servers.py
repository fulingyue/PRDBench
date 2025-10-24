#!/usr/bin/env python3
"""
Local MCP Server Implementation
Provides Python interpreter, file operations, and system operations services
"""

import asyncio
import json
import logging
import subprocess
import tempfile
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

import aiohttp
from aiohttp import web
import pexpect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from mcp_config import (
    PYTHON_INTERPRETER_MCP_URL, 
    FILE_OPERATIONS_PORT,
    PYTHON_INTERPRETER_PORT,
    SYSTEM_OPERATIONS_PORT,
    FILE_OPERATIONS_MCP_URL, 
    SYSTEM_OPERATIONS_MCP_URL,
    WORKSPACE_DIR,
)

class PythonInterpreterMCP:
    """Python Interpreter MCP Server"""
    TIMEOUT = 10
    
    def __init__(self, port: int = None):
        self.port = port or int(PYTHON_INTERPRETER_PORT)
        print(self.port)
        self.app = web.Application()
        self.setup_routes()
    
    def setup_routes(self):
        """Set up routes"""
        self.app.router.add_post('/python-interpreter/execute', self.execute_code)
        self.app.router.add_get('/python-interpreter/health', self.health_check)
        self.app.router.add_get('/python-interpreter/interactive', self.interactive_execute_code)
    
    async def execute_code(self, request):
        """Execute Python code"""
        try:
            data = await request.json()
            code = data.get('code', '')
            timeout = data.get('timeout', self.TIMEOUT)
            
            logger.info(f"Executing Python code: {code[:100]}...")
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute code
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd='/tmp'
                )
                
                response_data = {
                    'status': 'success',
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'return_code': result.returncode,
                    'execution_time': datetime.now().isoformat()
                }
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file)
            
            return web.json_response(response_data)
            
        except subprocess.TimeoutExpired:
            return web.json_response({
                'status': 'error',
                'error': 'Code execution timeout'
            }, status=408)
        except Exception as e:
            logger.error(f"Code execution error: {e}")
            return web.json_response({
                'status': 'error',
                'error': str(e)
            }, status=500)
    
    async def health_check(self, request):
        """Health check"""
        return web.json_response({
            'status': 'healthy',
            'service': 'python-interpreter',
            'timestamp': datetime.now().isoformat()
        })
    
    async def interactive_execute_code(self, request):
        """Interactive Python code execution (WebSocket)"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        # Start interactive Python process
        child = pexpect.spawn(sys.executable, ['-i'], encoding='utf-8', timeout=None)

        async def read_from_python():
            """Background task: continuously read Python output and push to frontend"""
            try:
                while True:
                    output = child.read_nonblocking(size=1024, timeout=1)
                    if output:
                        await ws.send_str(output)
            except pexpect.exceptions.TIMEOUT:
                pass
            except pexpect.exceptions.EOF:
                await ws.send_str('[Python process ended]')
                await ws.close()

        reader_task = asyncio.create_task(read_from_python())

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    # User input, write to Python process
                    child.sendline(msg.data)
                elif msg.type == web.WSMsgType.ERROR:
                    break
        finally:
            reader_task.cancel()
            child.terminate(force=True)
            await ws.close()
        return ws
    
    async def start(self):
        """Start server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        logger.info(f"Python Interpreter MCP Server started on port {self.port}")
        return runner

class FileOperationsMCP:
    """File Operations MCP Server"""
    
    def __init__(self, port: int = None, workspace_dir: str = None):
        self.port = port or int(FILE_OPERATIONS_PORT)
        self.workspace_dir = Path(workspace_dir or WORKSPACE_DIR)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        self.app = web.Application()
        self.setup_routes()
    
    def setup_routes(self):
        """Set up routes"""
        self.app.router.add_post('/file-operations/read', self.read_file)
        self.app.router.add_post('/file-operations/write', self.write_file)
        self.app.router.add_post('/file-operations/list', self.list_files)
        self.app.router.add_get('/file-operations/health', self.health_check)
    
    def validate_path(self, file_path: str) -> bool:
        """Validate if file path is safe"""
        try:
            file_path = Path(file_path).resolve()
            workspace_path = self.workspace_dir.resolve()
            return str(file_path).startswith(str(workspace_path))
        except:
            return False
    
    async def read_file(self, request):
        """Read file"""
        try:
            data = await request.json()
            file_path = data.get('path', '')
            
            if not self.validate_path(file_path):
                return web.json_response({
                    'status': 'error',
                    'error': 'File path is not safe'
                }, status=403)
            
            file_path = Path(file_path)
            if not file_path.exists():
                return web.json_response({
                    'status': 'error',
                    'error': 'File does not exist'
                }, status=404)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return web.json_response({
                'status': 'success',
                'content': content,
                'size': len(content),
                'path': str(file_path)
            })
            
        except Exception as e:
            logger.error(f"File reading error: {e}")
            return web.json_response({
                'status': 'error',
                'error': str(e)
            }, status=500)
    
    async def write_file(self, request):
        """Write file"""
        try:
            data = await request.json()
            file_path = data.get('path', '')
            content = data.get('content', '')
            
            if not self.validate_path(file_path):
                return web.json_response({
                    'status': 'error',
                    'error': 'File path is not safe'
                }, status=403)
            
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return web.json_response({
                'status': 'success',
                'path': str(file_path),
                'size': len(content)
            })
            
        except Exception as e:
            logger.error(f"File writing error: {e}")
            return web.json_response({
                'status': 'error',
                'error': str(e)
            }, status=500)
    
    async def list_files(self, request):
        """List files"""
        try:
            data = await request.json()
            directory = data.get('directory', str(self.workspace_dir))
            
            if not self.validate_path(directory):
                return web.json_response({
                    'status': 'error',
                    'error': 'Directory path is not safe'
                }, status=403)
            
            directory = Path(directory)
            if not directory.exists():
                return web.json_response({
                    'status': 'error',
                    'error': 'Directory does not exist'
                }, status=404)
            
            files = []
            for item in directory.iterdir():
                file_info = {
                    'name': item.name,
                    'type': 'directory' if item.is_dir() else 'file',
                    'size': item.stat().st_size if item.is_file() else None
                }
                files.append(file_info)
            
            return web.json_response({
                'status': 'success',
                'files': files,
                'directory': str(directory)
            })
            
        except Exception as e:
            logger.error(f"File listing error: {e}")
            return web.json_response({
                'status': 'error',
                'error': str(e)
            }, status=500)
    
    async def health_check(self, request):
        """Health check"""
        return web.json_response({
            'status': 'healthy',
            'service': 'file-operations',
            'workspace': str(self.workspace_dir),
            'timestamp': datetime.now().isoformat()
        })
    
    async def start(self):
        """Start server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        logger.info(f"File Operations MCP Server started on port {self.port}")
        return runner

async def start_all_servers():
    """Start all MCP servers"""
    servers = [
        PythonInterpreterMCP(),
        FileOperationsMCP(),
    ]
    
    runners = []
    for server in servers:
        runner = await server.start()
        runners.append(runner)
    
    logger.info("All MCP servers have been started")
    
    try:
        # Keep servers running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down servers...")
        for runner in runners:
            await runner.cleanup()
        logger.info("All servers have been shut down")

if __name__ == "__main__":
    asyncio.run(start_all_servers()) 