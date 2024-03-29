while true; do
  nc -l <desired_port> | {
    while read line; do
      case "$line" in
        <desired_token> )
          cd <project_files_directory>;
          python3 main.py;;
      esac
    done
  }
done