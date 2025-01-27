from playsound import playsound


def play_file(filename: str):
    try:
        playsound(filename)

    except Exception:
        print('ERROR sound.play_file', filename)

        return None
