# Project PlasmoDocking

The PlasmoDocking Project is an automated solution for performing virtual ligand docking against a variety of receptors, specifically designed to identify promising interactions in biomedical research. Utilizing a combination of bioinformatics and computational chemistry tools, this project facilitates large-scale analysis of potential ligand-receptor interactions.

## PlasmoDocking with Docker

The PlasmoDocking Project uses Docker to simplify the configuration and execution of the necessary environment for scalable and efficient molecular docking. With Docker, the required dependencies and tools, including MGLTools, Open Babel, and AutoDock-GPU, are encapsulated in containers, making deployment easy and ensuring a consistent execution environment.

### Docker Configuration

The project contains two main Dockerfiles:

1. **DockerFile.Worker:** This Dockerfile sets up the environment required to run the Celery worker, including the installation of MGLTools, Open Babel, and AutoDock-GPU. This container processes queued docking tasks, utilizing GPU power when available.

2. **DockerFile:** This Dockerfile sets up the environment to run the Django server, which manages the project's web interface and the API for submitting and monitoring docking tasks.

### Using Celery and RabbitMQ

Celery is a distributed task queue system used to process docking tasks asynchronously and scalably. In PlasmoDocking, Celery is configured to work with RabbitMQ as the message broker, managing the distribution of tasks among the available workers.

**Celery:** Enables parallel and distributed execution of docking simulations, significantly improving processing efficiency and speed, especially when combined with GPU execution.

**RabbitMQ:** Acts as an intermediary between the Django server and the Celery workers, queuing docking tasks submitted through the web interface or API and distributing them to the workers for processing.

## Quick Start

To start the PlasmoDocking process, you need an `.sdf` file containing the ligands of interest (currently, a maximum of 10 ligands in the `.sdf` file is allowed for processing). The automated system will process this file through various stages to identify the best binding energies with the available receptors.

## Using the Tools

### MGLTools

MGLTools is a software suite that provides tools for visualization, analysis, and preparation of molecules for docking simulations. In the PlasmoDocking Project, MGLTools is primarily used to convert ligands from `.pdb` to `.pdbqt` format, preparing them for the docking process with AutoDock-GPU. This step is crucial for defining the active atoms of the ligands and the possible flexibilities of the molecules.

**Ligand Preparation Steps:**

1. **Format Conversion:** Ligands separated from the `.sdf` file are converted to `.pdb` using Open Babel.
2. **Docking Preparation:** Using the `prepare_ligand4.py` script from MGLTools, ligands in `.pdb` format are processed to generate `.pdbqt` files, containing information about atomic charges, atom types, and potential flex points of the molecules.

### Open Babel

Open Babel is a computational chemistry tool used to convert molecular data between different file formats. In the project, Open Babel is used for two main tasks:

1. **Ligand Splitting:** From the provided `.sdf` file, Open Babel separates individual ligands for independent processing.
2. **Format Conversion:** Transforms ligands from `.sdf` to `.pdb` and subsequently converts docking results from `.pdbqt` to `.pdb`, facilitating visualization and analysis.

### AutoDock-GPU

AutoDock-GPU is an optimized version of AutoDock, one of the most widely used software for molecular docking, leveraging GPU power to significantly speed up calculations. In PlasmoDocking, AutoDock-GPU is responsible for performing ligand docking against selected receptors, calculating binding energies, and determining the best conformation for each ligand-receptor pair.

**Docking Execution:**

1. **Receptor Preparation:** Receptors are pre-prepared and stored in the database, including the generation of grid maps necessary for docking.
2. **Automated Docking:** For each ligand-receptor pair, AutoDock-GPU is run using the ligands' `.pdbqt` files and the receptors' grid maps to simulate docking. This process is performed in parallel for all ligands against all available receptors.
3. **Result Analysis:** After docking execution, the best binding energies are extracted, allowing the identification of the most promising interactions.

These tools together form the backbone of the PlasmoDocking process, enabling large-scale analysis of potential ligand-receptor interactions with efficiency and precision.

## PlasmoDocking Process: Detailed Flowchart

### 1. Receiving the `.sdf` File

The process begins with the user providing an `.sdf` file containing various ligand structures.

### 2. Directory Creation

Based on the user and process name, specific directories are created to store macromolecules (receptors), ligands, docking results, and other necessary files.

### 3. Splitting Ligands from the `.sdf`

The `.sdf` file is split to separate individual ligands using tools like Open Babel.

### 4. Ligand Preparation: `.sdf` to `.pdb`

The separated ligands are converted from `.sdf` to `.pdb`, facilitating subsequent manipulations.

### 5. Ligand Preparation for `.pdbqt`

Using MGLTools, ligands in `.pdb` format are prepared for the `.pdbqt` format, suitable for the docking process.

### 6. Receptor Query from the Database

All available receptors in the database (approximately 39) are selected to participate in the docking process.

### 7. Docking Execution

For each ligand-receptor pair, AutoDock-GPU is used to perform docking, exploring conformations and calculating binding energies.

**Example:** An `.sdf` file with 10 ligands is submitted for the process. Each ligand will undergo docking with each receptor. In this example, a total of 390 molecular docking processes will be executed with AutoDock-GPU using the parameter `--nrun 50` (each molecular docking process is executed 50 times).

### 8. Result Analysis

From the docking results, the best binding energy for each receptor-ligand pair is extracted, identifying the most promising interactions.

### 9. Organizing Results

Results are organized into specific directories and compiled into a JSON file and a CSV file, facilitating subsequent analyses.

### 10. Interactive Dashboard and 3D Visualization

The frontend application accessible at "www.plasmodocking-labioquim.unir.br" offers an interactive dashboard for result analysis. Through this dashboard, users can view data in various formats, including tables and charts, facilitating result interpretation. Additionally, users can visualize ligand-receptor complex structures in 3D using NGL Viewer, providing deeper insights into molecular interactions.

## Conclusion

The PlasmoDocking Project represents a valuable tool for researchers in biochemistry and pharmacology, simplifying the process of identifying promising ligands for a wide range of receptors. The automation and efficiency of the process enable large-scale analysis, potentially accelerating the discovery of new drug candidates.