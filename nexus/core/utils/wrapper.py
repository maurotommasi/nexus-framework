import functools
import inspect
import time
import traceback
from typing import Callable, List, Any, Dict, Optional, Union
from datetime import datetime
from enum import Enum

from nexus.core.utils import LogManager, TimeUtils, SystemUtils

class LogLevel(Enum):
    """Log levels for the wrapper."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    SYSTEM = "SYSTEM"
    LAYER = "LAYER"

class ExecutionContext:
    """Context object passed to pre/post hooks."""
    
    def __init__(self, func: Callable, args: tuple, kwargs: dict):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.start_time = time.time()
        self.end_time = None
        self.result = None
        self.exception = None
        self.metadata = {}
        self.logs = []
        
    @property
    def execution_time(self) -> float:
        """Get execution time in seconds."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
        # Examples:
        # ctx = ExecutionContext(lambda x: x, (1,), {})
        # ctx.end_time = ctx.start_time + 2
        # ctx.execution_time -> 2.0

    @property
    def function_name(self) -> str:
        """Get function name."""
        return f"{self.func.__module__}.{self.func.__name__}"
        # Examples:
        # ctx = ExecutionContext(lambda x: x, (1,), {})
        # ctx.function_name -> "__main__.<lambda>"

    @property
    def function_signature(self) -> str:
        """Get function signature."""
        sig = inspect.signature(self.func)
        return f"{self.func.__name__}{sig}"
        # Examples:
        # ctx = ExecutionContext(lambda a, b=2: a+b, (1,), {})
        # ctx.function_signature -> "<lambda>(a, b=2)"

    def add_log(self, level: LogLevel, message: str, data: Dict[str, Any] = None):
        """Add log entry to context."""
        self.logs.append({
            'timestamp': TimeUtils.get_timestamp(),
            'level': level.value,
            'message': message,
            'data': data or {}
        })
        # Examples:
        # ctx = ExecutionContext(lambda x: x, (1,), {})
        # ctx.add_log(LogLevel.INFO, "Test message")
        # ctx.logs -> [{'timestamp': '...', 'level': 'INFO', 'message': 'Test message', 'data': {}}]

    def set_metadata(self, key: str, value: Any):
        """Set metadata for the execution."""
        self.metadata[key] = value
        # Examples:
        # ctx = ExecutionContext(lambda x: x, (1,), {})
        # ctx.set_metadata("user", "alice")
        # ctx.metadata["user"] -> "alice"

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)
        # Examples:
        # ctx = ExecutionContext(lambda x: x, (1,), {})
        # ctx.set_metadata("role", "admin")
        # ctx.get_metadata("role") -> "admin"
        # ctx.get_metadata("missing", "default") -> "default"

class FunctionWrapper:
    """Advanced function wrapper with pre/post hooks and specialized logging."""
    
    def __init__(self, name: str = None, logger_name: str = "wrapper"):
        self.name = name
        self.logger = LogManager().get_logger(logger_name)
        self.pre_hooks: List[Callable[[ExecutionContext], None]] = []
        self.post_hooks: List[Callable[[ExecutionContext], None]] = []
        self.error_hooks: List[Callable[[ExecutionContext], None]] = []
        self.log_config = {
            'log_entry': True,
            'log_exit': True,
            'log_args': True,
            'log_result': True,
            'log_execution_time': True,
            'log_system_info': False,
            'log_layer_info': False,
            'sensitive_params': []
        }
        # Examples:
        # wrapper = FunctionWrapper(name="test")
        # wrapper.log_config["log_entry"] -> True

    def configure_logging(self, **config):
        """Configure logging options."""
        self.log_config.update(config)
        return self
        # Examples:
        # wrapper = FunctionWrapper().configure_logging(log_entry=False)
        # wrapper.log_config["log_entry"] -> False

    def add_pre_hook(self, hook: Callable[[ExecutionContext], None]):
        """Add pre-execution hook."""
        self.pre_hooks.append(hook)
        return self
        # Examples:
        # wrapper = FunctionWrapper()
        # wrapper.add_pre_hook(lambda ctx: ctx.set_metadata("pre", True))
        # -> hook added to pre_hooks

    def add_post_hook(self, hook: Callable[[ExecutionContext], None]):
        """Add post-execution hook."""
        self.post_hooks.append(hook)
        return self
        # Examples:
        # wrapper = FunctionWrapper()
        # wrapper.add_post_hook(lambda ctx: ctx.set_metadata("post", True))
        # -> hook added to post_hooks

    def add_error_hook(self, hook: Callable[[ExecutionContext], None]):
        """Add error handling hook."""
        self.error_hooks.append(hook)
        return self
        # Examples:
        # wrapper = FunctionWrapper()
        # wrapper.add_error_hook(lambda ctx: ctx.set_metadata("error", True))
        # -> hook added to error_hooks

    def add_debug_hooks(self):
        """Add standard debug hooks."""
        self.add_pre_hook(self._debug_entry_hook)
        self.add_post_hook(self._debug_exit_hook)
        self.add_error_hook(self._debug_error_hook)
        return self
        # Examples:
        # wrapper = FunctionWrapper().add_debug_hooks()
        # -> debug hooks added automatically

    def add_system_hooks(self):
        """Add system monitoring hooks."""
        self.add_pre_hook(self._system_pre_hook)
        self.add_post_hook(self._system_post_hook)
        return self
        # Examples:
        # wrapper = FunctionWrapper().add_system_hooks()
        # -> system monitoring hooks added

    def add_layer_hooks(self, layer_name: str):
        """Add layer-specific hooks."""
        def layer_pre_hook(context: ExecutionContext):
            context.add_log(LogLevel.LAYER, f"[{layer_name.upper()}] Starting {context.function_name}")
            context.set_metadata('layer', layer_name)
        
        def layer_post_hook(context: ExecutionContext):
            status = "SUCCESS" if context.exception is None else "FAILED"
            context.add_log(LogLevel.LAYER, f"[{layer_name.upper()}] {status} {context.function_name}")
        
        self.add_pre_hook(layer_pre_hook)
        self.add_post_hook(layer_post_hook)
        return self
        # Examples:
        # wrapper = FunctionWrapper().add_layer_hooks("api")
        # -> adds hooks logging start and end of "api" layer functions

    def add_performance_hooks(self, threshold_ms: float = 1000.0):
        """Add performance monitoring hooks."""
        def performance_hook(context: ExecutionContext):
            execution_time_ms = context.execution_time * 1000
            if execution_time_ms > threshold_ms:
                context.add_log(
                    LogLevel.WARNING, 
                    f"Slow execution detected: {context.function_name}",
                    {'execution_time_ms': execution_time_ms, 'threshold_ms': threshold_ms}
                )
        
        self.add_post_hook(performance_hook)
        return self
        # Examples:
        # wrapper = FunctionWrapper().add_performance_hooks(threshold_ms=500)
        # -> logs warning if function takes > 500ms

    def add_audit_hooks(self, audit_level: str = "INFO"):
        """Add audit logging hooks."""
        def audit_hook(context: ExecutionContext):
            audit_data = {
                'function': context.function_name,
                'timestamp': TimeUtils.get_timestamp(),
                'args_count': len(context.args),
                'kwargs_count': len(context.kwargs),
                'execution_time': context.execution_time,
                'success': context.exception is None
            }
            level = LogLevel(audit_level.upper())
            context.add_log(level, f"AUDIT: {context.function_name}", audit_data)
        
        self.add_post_hook(audit_hook)
        return self
        # Examples:
        # wrapper = FunctionWrapper().add_audit_hooks("INFO")
        # -> audit logs added after execution

    def __call__(self, func: Callable) -> Callable:
        """Main decorator function."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            context = ExecutionContext(func, args, kwargs)
            try:
                self._execute_hooks(self.pre_hooks, context, "pre")
                if self.log_config['log_entry']:
                    self._log_function_entry(context)
                context.result = func(*args, **kwargs)
                context.end_time = time.time()
                self._execute_hooks(self.post_hooks, context, "post")
                if self.log_config['log_exit']:
                    self._log_function_exit(context)
                return context.result
            except Exception as e:
                context.exception = e
                context.end_time = time.time()
                self._execute_hooks(self.error_hooks, context, "error")
                self._log_function_error(context)
                raise
            finally:
                self._flush_context_logs(context)
        wrapper._nexus_wrapper = self
        wrapper._nexus_original = func
        return wrapper
        # Examples:
        # @FunctionWrapper().add_debug_hooks()
        # def add(x, y): return x + y
        # add(2, 3) -> 5 with debug logs

# Convenience decorators and factory functions
def nexus_wrapper(name: str = None, **config) -> FunctionWrapper:
    """Create a new FunctionWrapper instance."""
    return FunctionWrapper(name=name).configure_logging(**config)
    # Examples:
    # @nexus_wrapper()
    # def hello(): return "hi"
    # hello() -> "hi"

def debug_wrapper(**config):
    """Quick debug wrapper with standard debug hooks."""
    return nexus_wrapper(**config).add_debug_hooks()
    # Examples:
    # @debug_wrapper()
    # def add(x, y): return x + y
    # add(1, 2) -> 3 with debug logs

def system_wrapper(**config):
    """Quick system monitoring wrapper."""
    return nexus_wrapper(**config).add_system_hooks()
    # Examples:
    # @system_wrapper()
    # def multiply(x, y): return x * y
    # multiply(2, 3) -> 6 with system monitoring logs

def layer_wrapper(layer_name: str, **config):
    """Quick layer-specific wrapper."""
    return nexus_wrapper(**config).add_layer_hooks(layer_name)
    # Examples:
    # @layer_wrapper("database")
    # def query_db(): return "ok"
    # query_db() -> "ok" with layer logs

def performance_wrapper(threshold_ms: float = 1000.0, **config):
    """Quick performance monitoring wrapper."""
    return nexus_wrapper(**config).add_performance_hooks(threshold_ms)
    # Examples:
    # @performance_wrapper(threshold_ms=100)
    # def slow(): time.sleep(0.2); return "done"
    # slow() -> "done" with performance warning

def audit_wrapper(audit_level: str = "INFO", **config):
    """Quick audit logging wrapper."""
    return nexus_wrapper(**config).add_audit_hooks(audit_level)
    # Examples:
    # @audit_wrapper("INFO")
    # def process(): return True
    # process() -> True with audit logs

# Custom hook examples
def custom_validation_hook(required_params: List[str]):
    """Custom hook to validate required parameters."""
    def hook(context: ExecutionContext):
        missing_params = []
        for param in required_params:
            if param not in context.kwargs or context.kwargs[param] is None:
                missing_params.append(param)
        if missing_params:
            context.add_log(LogLevel.ERROR, f"Validation failed for {context.function_name}", {'missing_params': missing_params})
            raise ValueError(f"Missing required parameters: {missing_params}")
    return hook
    # Examples:
    # hook = custom_validation_hook(["user"])
    # ctx = ExecutionContext(lambda x: x, (), {"id": 1})
    # hook(ctx) -> raises ValueError("Missing required parameters: ['user']")

def custom_caching_hook(cache_key_func: Callable = None):
    """Custom hook for simple caching."""
    cache = {}
    def pre_hook(context: ExecutionContext):
        if cache_key_func:
            cache_key = cache_key_func(*context.args, **context.kwargs)
        else:
            cache_key = f"{context.function_name}:{hash(str(context.args) + str(context.kwargs))}"
        context.set_metadata('cache_key', cache_key)
        if cache_key in cache:
            context.result = cache[cache_key]
            context.set_metadata('cache_hit', True)
            context.add_log(LogLevel.DEBUG, f"Cache hit for {context.function_name}")
    def post_hook(context: ExecutionContext):
        if not context.get_metadata('cache_hit', False):
            cache_key = context.get_metadata('cache_key')
            cache[cache_key] = context.result
            context.add_log(LogLevel.DEBUG, f"Cached result for {context.function_name}")
    return pre_hook, post_hook
    # Examples:
    # pre_hook, post_hook = custom_caching_hook()
    # ctx = ExecutionContext(lambda x: x, (1,), {})
    # ctx.result = 5; post_hook(ctx)
    # ctx.get_metadata('cache_key') in pre_hook.__closure__[0].cell_contents -> True