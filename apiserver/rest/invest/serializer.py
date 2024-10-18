def getDictByObject(input) -> dict:
    result: dict = {}

    for i in dir(input):
        if i[0:2] != '__':
            result.update({i: getattr(input, i)})

    return result
