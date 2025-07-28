import subprocess
import time
def ppmsQuery(strargs):
    args = strargs.split(' ')
    result = subprocess.run(
        [
            'C:/Users/ppms3user/.conda/envs/lab_env/python.exe',
            'C:/QdPpms/Data/Software_ZH/Measurement_notebooks/drivers/ppmsQuery.py',
        ]+list(args),
        capture_output=True,text=True
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return 0
# if __name__ == '__main__':
#     t0 = time.time()
#     result = ppmsQuery('GetDat?','6')
#     print(time.time()-t0)
#     print(result)