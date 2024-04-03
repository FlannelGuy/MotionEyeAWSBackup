import os
from cryptography.fernet import Fernet
from config import Config
from pathlib import Path, PurePath, PurePosixPath
import pysftp
import datetime
import main

cnopts = pysftp.CnOpts()
cnopts.hostkeys = None
awssftp = pysftp.Connection(host=Config.awsFtpHostname, username=Config.awsFtpUsername, private_key=Config.awsKey,
                            cnopts=cnopts)
awssftp.cwd(Config.awsRootDirectory)

def decryptFile(originalFile):
    # get key
    with open(Config.videoEncryptionKey, 'rb') as filekey:
        key = filekey.read()

    # using the key
    fernet = Fernet(key)

    # opening the encrypted file
    with open(originalFile, 'rb') as enc_file:
        encrypted = enc_file.read()

    # decrypting the file
    decrypted = fernet.decrypt(encrypted)

    # opening the file in write mode and
    # writing the decrypted data
    with open(originalFile, 'wb') as dec_file:
        dec_file.write(decrypted)


def downloadAll(localFilePath):
    if localFilePath is not None and checkLocalFilePath(localFilePath):
        print("download all to", localFilePath)
        awsDirectoriesAndFiles = main.getDirectoriesAndFiles(awssftp, Config.awsRootDirectory,
                                                        main.getDirectories(awssftp.listdir()))
        awssftp.cwd(Config.awsRootDirectory)
        for directory, downloadAllFilename in awsDirectoriesAndFiles:
            currentLocalFullDirectoryPath = Path(localFilePath).joinpath(directory).__str__()
            currentRemoteFullDirectoryPath = PurePosixPath(Config.awsRootDirectory).joinpath(directory).__str__()

            print(currentLocalFullDirectoryPath)
            print(currentRemoteFullDirectoryPath)

            if not Path(currentLocalFullDirectoryPath).exists():
                Path(currentLocalFullDirectoryPath).mkdir()

            remoteFullFileName = PurePosixPath(currentRemoteFullDirectoryPath).joinpath(downloadAllFilename).__str__()
            localFullFileName = PurePosixPath(currentLocalFullDirectoryPath).joinpath(downloadAllFilename).__str__()

            print(remoteFullFileName)
            print(localFullFileName)

            awssftp.get(remotepath=remoteFullFileName,
                             localpath=localFullFileName)
            decryptFile(localFullFileName)
    else:
        printFilePathWarning()

def help():
    print("""Help Menu
        help - print this message.
        list, ls - lists the dates that have videos on the AWS SFTP.
            param 1 - (optional) <date>:  date in format YYYY-MM-DD, alters 'ls' or 'list' behavior by listing videos 
            for download for that date.""")
    downloadHelp()


def downloadHelp():
    print("""\t\t'download' - downloads all or specific videos depending on parameters. Requires up to four parameters.
             param 1 - 
                '-f': designate the local filepath to download files, no download commands will work until a valid local
                    filepath to a directory is provided with this parameter.
                    param 1 - complete file path (don't escape any slashes or characters)
                '-a': downloads all available videos in their respective directories, locally
                '-s': download all videos from a <s>pecific date, or specific video from specific date. ( see param's )
                    param 1 - date in format YYYY-MM-DD (downloads all videos from that date if param 2 isn't provided )
                    param 2 - the video filename, including extension ( requires date as second param )
        """)

def checkLocalFilePath(localFilePath):
    if Path(localFilePath).exists():
        return True
    else:
        return False

def printDates():
    awssftp.cwd(Config.awsRootDirectory)
    directories = main.getDirectories(awssftp.listdir())
    for item in directories:
        print(item)


def printVideosFromSpecificDate(printVideosFromSpecificDatedate):
    awssftp.cwd(Config.awsRootDirectory)
    directories = main.getDirectories(awssftp.listdir())
    if directories.__contains__(printVideosFromSpecificDatedate):
        awssftp.cwd(PurePosixPath(Config.awsRootDirectory).joinpath(printVideosFromSpecificDatedate).__str__())
        print(awssftp.listdir())
        awssftp.cwd(Config.awsRootDirectory)
    else:
        print(date,"is not a date directory listed. run 'download -l' to find a valid date directory.")


def downloadSpecificVideo(localFilePath, downloadSpecificVideodate, filename):
    if localFilePath is not None and checkLocalFilePath(localFilePath):
        awssftp.cwd(Config.awsRootDirectory)
        directories = main.getDirectories(awssftp.listdir())
        downloadSpecificVideodate = downloadSpecificVideodate.__str__()
        print("testing", "valid filepath")
        if directories.__contains__(downloadSpecificVideodate):
            print("testing", "contains date")
            print(PurePosixPath(Config.awsRootDirectory).joinpath(downloadSpecificVideodate).joinpath(filename))
            if awssftp.exists(PurePosixPath(Config.awsRootDirectory).joinpath(downloadSpecificVideodate).joinpath(filename).__str__()):
                awssftp.cwd(PurePosixPath(Config.awsRootDirectory).joinpath(downloadSpecificVideodate).__str__())
                if not Path(localFilePath).joinpath(downloadSpecificVideodate).exists():
                    Path(localFilePath).joinpath(downloadSpecificVideodate).mkdir()
                print("testing", awssftp.listdir())
                if filename.endswith(Config.videoFileType):
                    awssftp.get(remotepath=PurePosixPath(Config.awsRootDirectory)
                                .joinpath(downloadSpecificVideodate).joinpath(filename).__str__(),
                                localpath=Path(localFilePath).joinpath(downloadSpecificVideodate).joinpath(
                                    filename).__str__())
                    decryptFile(
                        Path(localFilePath).joinpath(downloadSpecificVideodate).joinpath(filename).__str__())
            else:
                print(filename, "is not a valid filename for the date:", downloadSpecificVideodate)
        else:
            print(downloadSpecificVideodate,
                  "is not a date directory listed. run 'download -l' to find a valid date directory.")
    else:
        printFilePathWarning()
    awssftp.cwd(Config.awsRootDirectory)

def printFilePathWarning():
    print("""you need to specificy the full filename directory before you can download files.
            run "download -f <fullPathToFileDirectory>""")


def downloadVideosFromSpecificDate(localFilePath, downloadVideosFromSpecificDatedate):
    if localFilePath is not None and checkLocalFilePath(localFilePath):
        awssftp.cwd(Config.awsRootDirectory)
        directories = main.getDirectories(awssftp.listdir())
        downloadVideosFromSpecificDatedate = downloadVideosFromSpecificDatedate.__str__()
        print("testing", "valid filepath")
        if directories.__contains__(downloadVideosFromSpecificDatedate):
            print("testing","contains date")
            awssftp.cwd(PurePosixPath(Config.awsRootDirectory).joinpath(downloadVideosFromSpecificDatedate).__str__())
            if not Path(localFilePath).joinpath(downloadVideosFromSpecificDatedate).exists():
                Path(localFilePath).joinpath(downloadVideosFromSpecificDatedate).mkdir()
            print("testing",awssftp.listdir())
            for file in awssftp.listdir():
                if file.endswith(Config.videoFileType):
                    awssftp.get(remotepath=PurePosixPath(Config.awsRootDirectory)
                                .joinpath(downloadVideosFromSpecificDatedate).joinpath(file).__str__(),
                                localpath=Path(localFilePath).joinpath(downloadVideosFromSpecificDatedate).joinpath(file).__str__())
                    decryptFile(Path(localFilePath).joinpath(downloadVideosFromSpecificDatedate).joinpath(file).__str__())
            awssftp.cwd(Config.awsRootDirectory)
        else:
            print(downloadVideosFromSpecificDatedate, "is not a date directory listed. run 'download -l' to find a valid date directory.")
    else:
        printFilePathWarning()


if __name__ == '__main__':
    print("Welcome. Download and Decrypt your MotionEye videos.")
    userInput = []
    localFilePath = R""
    while True:
        print(">", end=" ")
        userInput = input().split()
        if len(userInput) != 0:

            if userInput[0] == "help":
                help()

            elif userInput[0].lower() == "download":
                if len(userInput) != 0:
                    try:
                        if len(userInput) == 2 and userInput[1].lower() == "-a":
                            if len(localFilePath) == 0:
                                printFilePathWarning()
                            else:
                                downloadAll(localFilePath)
                        elif 1 < len(userInput) < 2 and userInput[1].lower() == "-s":
                            downloadHelp()
                        elif len(userInput) == 3 and userInput[1].lower() == "-s":
                            if len(localFilePath) == 0:
                                printFilePathWarning()
                            else:
                                date = datetime.date.fromisoformat(userInput[2])
                                downloadVideosFromSpecificDate(localFilePath,date)
                        elif len(userInput) == 4 and userInput[1].lower() == "-s":
                            if len(localFilePath) == 0:
                                printFilePathWarning()
                            else:
                                date = datetime.date.fromisoformat(userInput[2])
                                filename = userInput[3]
                                downloadSpecificVideo(localFilePath, date, filename)
                        elif len(userInput) == 3 and userInput[1].lower() == "-f":
                            localFilePath = userInput[2]
                            if not checkLocalFilePath(localFilePath):
                                print(localFilePath, ": is not a valid filepath.")
                                localFilePath = R""
                        else:
                            downloadHelp()
                    except ValueError:
                        downloadHelp()

            elif userInput[0].lower() == "list" or userInput[0].lower() == "ls":
                if len(userInput) == 1:
                    print(main.getDirectories(awssftp.listdir()))
                elif len(userInput) == 2:
                    date = datetime.date.fromisoformat(userInput[1])
                    printVideosFromSpecificDate(date.__str__())
            elif userInput[0].lower() == "quit":
                awssftp.close()
                break
            else:
                help()
