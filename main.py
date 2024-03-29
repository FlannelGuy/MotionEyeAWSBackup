from pathlib import Path, PurePath, PurePosixPath

import pysftp
import datetime
from config import Config
from cryptography.fernet import Fernet


def getDirectories(rootDirectories):
    tempDirectoryList = []
    for item in rootDirectories:
        try:
            datetime.date.fromisoformat(item)
            tempDirectoryList.append(item)
        except ValueError:
            print(item, ": not a date directory.")
    return tempDirectoryList


def getDirectoriesAndFiles(sftp, rootDirectory, variableDirectories):
    tempFilesAndParentDirectory = []
    for directory in variableDirectories:
        sftp.cwd(PurePosixPath(rootDirectory).joinpath(directory))

        for file in sftp.listdir():
            if file.endswith(Config.videoFileType):
                tempFilesAndParentDirectory.append([directory, file])
    return tempFilesAndParentDirectory


def encryptFile(originalFile):
    # opening the key
    with open('filekey.key', 'rb') as filekey:
        key = filekey.read()

    # using the generated key
    fernet = Fernet(key)

    # opening the original file to encrypt
    with open(originalFile, 'rb') as file:
        original = file.read()

    # encrypting the file
    encrypted = fernet.encrypt(original)

    # opening the file in write mode and
    # writing the encrypted data
    with open(originalFile, 'wb') as encrypted_file:
        encrypted_file.write(encrypted)


def decryptFile(originalFile):
    # get key
    with open('filekey.key', 'rb') as filekey:
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


if __name__ == '__main__':
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    motionEyeFtp = pysftp.Connection(host=Config.motionEyeIpAddress, username=Config.motionEyeFtpUsername,
                                     password=Config.motionEyeFtpPassword, cnopts=cnopts)
    motionEyeFtp.cwd(Config.motionEyeLocalFtpFilePath)

    # get motionEye daily directories
    print("getting Motioneye directory and filenames.")
    motionEyeDirectoriesAndFiles = getDirectoriesAndFiles(motionEyeFtp, Config.motionEyeLocalFtpFilePath,
                                                          getDirectories(motionEyeFtp.listdir()))
    # collect names of aws FTP directories and their video files
    print("getting AWS directory and filenames.")
    awssftp = pysftp.Connection(host=Config.awsHostname, username=Config.awsFtpUsername, private_key=Config.awsKey,
                                cnopts=cnopts)
    awssftp.cwd(Config.awsRootDirectory)

    awsDirectoriesAndFiles = getDirectoriesAndFiles(awssftp, Config.awsRootDirectory, getDirectories(awssftp.listdir()))

    # compare lists to determine which are to be downloaded/transported to aws
    print("comparing MotionEye and AWS directory and filenames.")
    filesToTransport = []
    for item in motionEyeDirectoriesAndFiles.__iter__():
        if not awsDirectoriesAndFiles.__contains__(item):
            filesToTransport.append(item)

    # download files from motionEye to local server
    print("Downloading files from MotionEye that are not yet in the AWS SFTP.")
    for directory, filename in filesToTransport:

        currentLocalFullDirectoryPath = PurePosixPath(Config.temporaryServerFilePath).joinpath(directory).__str__()
        currentRemoteFullDirectoryPath = PurePosixPath(Config.motionEyeLocalFtpFilePath).joinpath(directory).__str__()

        if not Path(currentLocalFullDirectoryPath).exists():
            Path(currentLocalFullDirectoryPath).mkdir()

        remoteFullFileName = PurePosixPath(currentRemoteFullDirectoryPath).joinpath(filename).__str__()
        localFullFileName = PurePosixPath(currentLocalFullDirectoryPath).joinpath(filename).__str__()

        print(remoteFullFileName)
        print(localFullFileName)

        motionEyeFtp.get(remotepath=remoteFullFileName,
                         localpath=localFullFileName)

    # upload directories and files to aws
    print("Uploading files to AWS SFTP.")
    for directory, filename in filesToTransport:

        currentLocalFullDirectoryPath = PurePosixPath(Config.temporaryServerFilePath).joinpath(directory).__str__()
        currentRemoteFullDirectoryPath = PurePosixPath(Config.awsRootDirectory).joinpath(directory).__str__()

        if not awssftp.exists(currentRemoteFullDirectoryPath):
            awssftp.mkdir(currentRemoteFullDirectoryPath)

        remoteFullFileName = PurePosixPath(currentRemoteFullDirectoryPath).joinpath(filename).__str__()
        localFullFileName = PurePosixPath(currentLocalFullDirectoryPath).joinpath(filename).__str__()

        print(remoteFullFileName)
        print(localFullFileName)

        encryptFile(localFullFileName)
        awssftp.cwd(currentRemoteFullDirectoryPath)
        awssftp.put(localpath=localFullFileName,
                    remotepath=filename)

    awssftp.close()
    motionEyeFtp.close()
