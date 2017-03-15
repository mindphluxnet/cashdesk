def is_raspi():
    #: the file /sys/firmware/devicetree/base/model only exists on a Raspberry Pi
    #: and contains the exact model and revision
    #: just to be sure, we'll not only check for existance, but also check if the file
    #: actually contains the string "Raspberry Pi"
    try:
        f = open("/sys/firmware/devicetree/base/model")
        data = f.read()
        if "Raspberry Pi" in data:
            return True
        else:
            return False
    except Exception as e:
        return False
