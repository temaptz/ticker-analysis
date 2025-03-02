import subprocess

def is_docker():
    try:
        with open('/proc/self/mountinfo', 'r') as f:
            for line in f:
                if 'docker' in line:
                    return True

    except FileNotFoundError:
        return False

    return False


def get_df() -> str:
    try:
        result = subprocess.run(['df', '-h'], capture_output=True, text=True)
        result.check_returncode()
        return result.stdout

    except Exception as e:
        print('ERROR get_df', e)

    return ''


def get_uptime() -> str:
    try:
        result = subprocess.run(['uptime'], capture_output=True, text=True)
        result.check_returncode()
        return result.stdout

    except Exception as e:
        print('ERROR get_uptime', e)

    return ''
