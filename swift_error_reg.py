import lldb

def __lldb_init_module(debugger, dict):
    bp = debugger.GetDummyTarget().BreakpointCreateForException(lldb.eLanguageTypeSwift, False, True)
    # bp = debugger.GetDummyTarget().BreakpointCreateByName('swift_willThrow')
    bp.SetScriptCallbackFunction('{}.{}'.format(set_swifterr.__module__, set_swifterr.__name__))
    bp.SetAutoContinue(True)

def set_swifterr(frame, bp_loc, dict):
    # Map architecture to Swift error return register
    # https://github.com/apple/swift/blob/269d306b9d275aab5bd10f380a999e51901c5832/docs/ABI/RegisterUsage.md#L8
    def swift_error_register(arch):
        arch2error_reg = {
            'x86_64': 'r12',
            'x86_64h': 'r12',
            'arm64': 'x21',
            'arm64e': 'x21',
        }
        return arch2error_reg[arch]

    # Extract arch from target triple
    def arch(frame):
        return frame.GetThread().GetProcess().GetTarget().GetTriple().split('-')[0]

    # Get error register
    reg = frame.FindRegister(swift_error_register(arch(frame)))
    
    # Assign register value to user defined variable $swifterr
    result = frame.EvaluateExpression('{} $swifterr'.format(reg.GetTypeName()))
    result = frame.EvaluateExpression('$swifterr = {}'.format(reg.GetValue()))
    
    # GetError() returns 0x1001 if there is no result from an expression
    # https://github.com/llvm-mirror/lldb/blob/d01083a850f577b85501a0902b52fd0930de72c7/include/lldb/Expression/UserExpression.h#L269
    NO_RESULT = 0x1001
    if result.GetError().Fail() and not result.GetError().GetError() == NO_RESULT:
        print(result.GetError().GetCString())

    # No need to ever stop at this breakpoint
    return False
