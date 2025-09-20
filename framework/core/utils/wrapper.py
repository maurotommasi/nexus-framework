# framework/core/utils/wrapper.py
import functools
import inspect
import time
import traceback
from typing import Callable, List, Any, Dict, Optional, Union
from datetime import datetime
from enum import Enum

from framework.core.utils import LogManager, TimeUtils, SystemUtils

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
    
    @property
    def function_name(self) -> str:
        """Get function name."""
        return f"{self.func.__module__}.{self.func.__name__}"
    
    @property
    def function_signature(self) -> str:
        """Get function signature."""
        sig = inspect.signature(self.func)
        return f"{self.func.__name__}{sig}"
    
    def add_log(self, level: LogLevel, message: str, data: Dict[str, Any] = None):
        """Add log entry to context."""
        self.logs.append({
            'timestamp': TimeUtils.get_timestamp(),
            'level': level.value,
            'message': message,
            'data': data or {}
        })
    
    def set_metadata(self, key: str, value: Any):
        """Set metadata for the execution."""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)

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
            'sensitive_params': []  # Parameters to mask in logs
        }
    
    def configure_logging(self, **config):
        """Configure logging options."""
        self.log_config.update(config)
        return self
    
    def add_pre_hook(self, hook: Callable[[ExecutionContext], None]):
        """Add pre-execution hook."""
        self.pre_hooks.append(hook)
        return self
    
    def add_post_hook(self, hook: Callable[[ExecutionContext], None]):
        """Add post-execution hook."""
        self.post_hooks.append(hook)
        return self
    
    def add_error_hook(self, hook: Callable[[ExecutionContext], None]):
        """Add error handling hook."""
        self.error_hooks.append(hook)
        return self
    
    def add_debug_hooks(self):
        """Add standard debug hooks."""
        self.add_pre_hook(self._debug_entry_hook)
        self.add_post_hook(self._debug_exit_hook)
        self.add_error_hook(self._debug_error_hook)
        return self
    
    def add_system_hooks(self):
        """Add system monitoring hooks."""
        self.add_pre_hook(self._system_pre_hook)
        self.add_post_hook(self._system_post_hook)
        return self
    
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
    
    def __call__(self, func: Callable) -> Callable:
        """Main decorator function."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            context = ExecutionContext(func, args, kwargs)
            
            try:
                # Execute pre-hooks
                self._execute_hooks(self.pre_hooks, context, "pre")
                
                # Log function entry
                if self.log_config['log_entry']:
                    self._log_function_entry(context)
                
                # Execute the actual function
                context.result = func(*args, **kwargs)
                context.end_time = time.time()
                
                # Execute post-hooks
                self._execute_hooks(self.post_hooks, context, "post")
                
                # Log function exit
                if self.log_config['log_exit']:
                    self._log_function_exit(context)
                
                return context.result
                
            except Exception as e:
                context.exception = e
                context.end_time = time.time()
                
                # Execute error hooks
                self._execute_hooks(self.error_hooks, context, "error")
                
                # Log error
                self._log_function_error(context)
                
                # Re-raise the exception
                raise
            
            finally:
                # Log all context logs
                self._flush_context_logs(context)
        
        # Store wrapper configuration on the function
        wrapper._nexus_wrapper = self
        wrapper._nexus_original = func
        
        return wrapper
    
    def _execute_hooks(self, hooks: List[Callable], context: ExecutionContext, hook_type: str):
        """Execute a list of hooks safely."""
        for hook in hooks:
            try:
                hook(context)
            except Exception as e:
                self.logger.error(f"Hook execution failed ({hook_type}): {str(e)}")
    
    def _log_function_entry(self, context: ExecutionContext):
        """Log function entry."""
        message = f"➤ {context.function_name}"
        
        log_data = {}
        
        if self.log_config['log_args'] and (context.args or context.kwargs):
            # Mask sensitive parameters
            masked_kwargs = self._mask_sensitive_data(context.kwargs)
            log_data['args_count'] = len(context.args)
            log_data['kwargs'] = masked_kwargs
        
        if self.log_config['log_system_info']:
            log_data['system_info'] = {
                'cpu_count': SystemUtils.get_system_info()['cpu_count'],
                'memory_usage': SystemUtils.get_memory_usage()['virtual']['percent']
            }
        
        self.logger.info(message, extra={'data': log_data} if log_data else None)
    
    def _log_function_exit(self, context: ExecutionContext):
        """Log function exit."""
        message = f"✓ {context.function_name}"
        
        log_data = {}
        
        if self.log_config['log_execution_time']:
            log_data['execution_time'] = TimeUtils.format_duration(context.execution_time)
        
        if self.log_config['log_result'] and context.result is not None:
            # Only log simple results to avoid huge logs
            if isinstance(context.result, (str, int, float, bool, list, dict)):
                if isinstance(context.result, (list, dict)):
                    log_data['result_type'] = type(context.result).__name__
                    log_data['result_size'] = len(context.result)
                else:
                    log_data['result'] = context.result
        
        self.logger.info(message, extra={'data': log_data} if log_data else None)
    
    def _log_function_error(self, context: ExecutionContext):
        """Log function error."""
        message = f"✗ {context.function_name}"
        
        log_data = {
            'error': str(context.exception),
            'error_type': type(context.exception).__name__,
            'execution_time': TimeUtils.format_duration(context.execution_time),
            'traceback': traceback.format_exc()
        }
        
        self.logger.error(message, extra={'data': log_data})
    
    def _flush_context_logs(self, context: ExecutionContext):
        """Flush all context logs."""
        for log_entry in context.logs:
            level = log_entry['level'].lower()
            log_method = getattr(self.logger, level, self.logger.info)
            log_method(log_entry['message'], extra={'data': log_entry['data']} if log_entry['data'] else None)
    
    def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive parameters in logs."""
        if not self.log_config.get('sensitive_params'):
            return data
        
        masked_data = data.copy()
        for param in self.log_config['sensitive_params']:
            if param in masked_data:
                masked_data[param] = "***MASKED***"
        
        return masked_data
    
    # Standard hook implementations
    def _debug_entry_hook(self, context: ExecutionContext):
        """Standard debug entry hook."""
        context.add_log(
            LogLevel.DEBUG,
            f"DEBUG: Entering {context.function_signature}",
            {
                'args_count': len(context.args),
                'kwargs_keys': list(context.kwargs.keys())
            }
        )
    
    def _debug_exit_hook(self, context: ExecutionContext):
        """Standard debug exit hook."""
        context.add_log(
            LogLevel.DEBUG,
            f"DEBUG: Exiting {context.function_name}",
            {
                'execution_time_ms': context.execution_time * 1000,
                'result_type': type(context.result).__name__ if context.result is not None else None
            }
        )
    
    def _debug_error_hook(self, context: ExecutionContext):
        """Standard debug error hook."""
        context.add_log(
            LogLevel.DEBUG,
            f"DEBUG: Error in {context.function_name}",
            {
                'error_type': type(context.exception).__name__,
                'error_message': str(context.exception)
            }
        )
    
    def _system_pre_hook(self, context: ExecutionContext):
        """System monitoring pre-hook."""
        system_info = {
            'memory_percent': SystemUtils.get_memory_usage()['virtual']['percent'],
            'cpu_percent': SystemUtils.get_cpu_usage(interval=0.1)['overall_percent']
        }
        context.set_metadata('system_pre', system_info)
        
        context.add_log(
            LogLevel.SYSTEM,
            f"SYSTEM: Pre-execution state for {context.function_name}",
            system_info
        )
    
    def _system_post_hook(self, context: ExecutionContext):
        """System monitoring post-hook."""
        system_info = {
            'memory_percent': SystemUtils.get_memory_usage()['virtual']['percent'],
            'cpu_percent': SystemUtils.get_cpu_usage(interval=0.1)['overall_percent']
        }
        
        pre_info = context.get_metadata('system_pre', {})
        
        # Calculate resource usage delta
        memory_delta = system_info['memory_percent'] - pre_info.get('memory_percent', 0)
        cpu_delta = system_info['cpu_percent'] - pre_info.get('cpu_percent', 0)
        
        context.add_log(
            LogLevel.SYSTEM,
            f"SYSTEM: Post-execution state for {context.function_name}",
            {
                **system_info,
                'memory_delta': round(memory_delta, 2),
                'cpu_delta': round(cpu_delta, 2),
                'execution_time_ms': context.execution_time * 1000
            }
        )

# Convenience decorators and factory functions
def nexus_wrapper(name: str = None, **config) -> FunctionWrapper:
    """Create a new FunctionWrapper instance."""
    return FunctionWrapper(name=name).configure_logging(**config)

def debug_wrapper(**config):
    """Quick debug wrapper with standard debug hooks."""
    return nexus_wrapper(**config).add_debug_hooks()

def system_wrapper(**config):
    """Quick system monitoring wrapper."""
    return nexus_wrapper(**config).add_system_hooks()

def layer_wrapper(layer_name: str, **config):
    """Quick layer-specific wrapper."""
    return nexus_wrapper(**config).add_layer_hooks(layer_name)

def performance_wrapper(threshold_ms: float = 1000.0, **config):
    """Quick performance monitoring wrapper."""
    return nexus_wrapper(**config).add_performance_hooks(threshold_ms)

def audit_wrapper(audit_level: str = "INFO", **config):
    """Quick audit logging wrapper."""
    return nexus_wrapper(**config).add_audit_hooks(audit_level)

# Custom hook examples
def custom_validation_hook(required_params: List[str]):
    """Custom hook to validate required parameters."""
    def hook(context: ExecutionContext):
        missing_params = []
        for param in required_params:
            if param not in context.kwargs or context.kwargs[param] is None:
                missing_params.append(param)
        
        if missing_params:
            context.add_log(
                LogLevel.ERROR,
                f"Validation failed for {context.function_name}",
                {'missing_params': missing_params}
            )
            raise ValueError(f"Missing required parameters: {missing_params}")
    
    return hook

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