from abc import ABC, abstractmethod
from typing import List
from PIL.Image import Image

class AssignmentVisualizer(ABC):
    @abstractmethod
    def visualize(self, images: List[Image], pdf_name: str, validator_text: str) -> str | None:
        """
        Visualizes the assignment validation results.
        
        :param images: List of PIL Image objects extracted from the PDF.
        :param pdf_name: The name or path of the PDF.
        :param validator_text: The evaluation result text from the validator agent.
        :return: Path to the generated visualizer output, or None.
        """
        pass

    @abstractmethod
    def generate_front_page(self, model: str, pages_per_assignment: int, folder: str, start_time: str, end_time: str, successful_count: int, last_assignment: str, prompt_text: str, parsed_files: List[str] = None) -> str:
        """
        Generates a front page summarizing the batch processing.
        
        :param model: The name of the model used.
        :param pages_per_assignment: Number of expected pages per assignment.
        :param folder: The directory containing the processed PDFs.
        :param start_time: Execution start time.
        :param end_time: Execution completion time.
        :param successful_count: Number of successfully processed assignments.
        :param last_assignment: Filename of the last processed assignment.
        :param prompt_text: The evaluation prompt template used.
        :param parsed_files: A list of filenames or paths to the individual generated visualization HTML files.
        :return: Generated front page content.
        """
        pass
