import os

def create_folder(folderName, ifCheck=False):
    if not os.path.exists(folderName):
        os.makedirs(folderName)
    elif ifCheck:
        print(folderName, "folder already exist, do you want to continue?")
        userInput = input("Yes/No:")
        if (userInput.lower() == "no"):
            exit(0)

def get_num_files_in_dir(dir):
    dir_contents = os.listdir(dir)
    files = [item for item in dir_contents if os.path.isfile(os.path.join(dir, item))]
    return len(files)