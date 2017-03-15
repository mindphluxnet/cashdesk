def is_raspi():

    try:
        f = open("/sys/firmware/devicetree/base/model")
        data = f.read()
        if "Raspberry Pi" in data:
            return True
        else:
            return False
    except Exception as e:
        return False
