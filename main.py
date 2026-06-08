from inky.auto import auto


def main():
    print("Hello from inky-dashboard!")
    display = auto()
    print(f"Display specs:\nColour: {display.colour}\nResolution: {display.resolution}")


if __name__ == "__main__":
    main()
