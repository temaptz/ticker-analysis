def is_docker():
    try:
        with open('/proc/self/mountinfo', 'r') as f:
            for line in f:
                if 'docker' in line:
                    return True

    except FileNotFoundError:
        return False

    return False
