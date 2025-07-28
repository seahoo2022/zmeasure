import subprocess
import ctypes
import argparse
ppmsdll = ctypes.WinDLL('C:/Windows/SysWOW64/ppmscomm.dll')
#ppmsdll.

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('args',nargs='*')
    parsed_args = parser.parse_args()
    listArgs = parsed_args.args
    arg = ' '.join(listArgs)
    c_arg = ctypes.c_char_p(arg.encode('utf-8'))
    print(arg)
    response = ctypes.create_string_buffer(4096)
    errors = ctypes.create_string_buffer(256)
    errorCode = ctypes.c_int32(0)
    errorCode_ptr = ctypes.pointer(errorCode)
    ppms_eror = ctypes.c_int16(0)
    ppms_errorCode_ptr = ctypes.pointer(ppms_eror)
    print(ppmsdll.GpibSend(15,
                           c_arg,
                           len(arg),
                           response,
                           4096,
                           errorCode_ptr,
                           ppms_errorCode_ptr,
                           errors,
                           256,
                           0,
                           10000))
    print('response=',response.value)
    print('errorStr=',errors.value)