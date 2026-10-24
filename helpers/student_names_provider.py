import os

class StudentNamesProvider:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def get_students(self) -> str:
        """
        Reads the .txt file of students, stripping whitespace,
        ignoring empty lines, and returns a comma-separated list of names.
        """
        get_students_as_list = self.get_students_as_list()
        return ", ".join(get_students_as_list)

    def get_students_as_list(self) -> list[str]:
        """
        Reads the .txt file of students, stripping whitespace,
        ignoring empty lines, and returns a list of names.
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        with open(self.file_path, 'r', encoding='utf-8') as f:
            # Read lines, strip whitespace, and filter out any empty lines
            lines = [line.strip() for line in f.readlines() if line.strip()]
        print(f"Loaded {len(lines)} student names from {self.file_path}.")
        return lines
    def get_students_as_list_ordered(self) -> list[tuple[int, str]]:
            """
            Reads the .txt file of students, stripping whitespace,
            ignoring empty lines, and returns a list of names.
            """
            if not os.path.exists(self.file_path):
                raise FileNotFoundError(f"File not found: {self.file_path}")
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                # Read lines, strip whitespace, and filter out any empty lines
                lines = [line.strip() for line in f.readlines() if line.strip()]
            print(f"Loaded {len(lines)} student names from {self.file_path}.")

            res = list(enumerate(lines, start=0))
            print(f"Created ordered list of student names with indices from {self.file_path}.")
            return res
