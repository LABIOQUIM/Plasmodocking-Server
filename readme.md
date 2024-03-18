# Projeto PlasmoDocking

O Projeto PlasmoDocking é uma solução automatizada para realizar docking virtual de ligantes contra uma variedade de receptores, especificamente desenhado para identificar interações promissoras em pesquisas biomédicas. Utilizando uma combinação de ferramentas de bioinformática e química computacional, este projeto facilita a análise em larga escala de potenciais interações ligante-receptor.

## PlasmoDocking com Docker

O Projeto PlasmoDocking utiliza Docker para simplificar a configuração e execução do ambiente necessário para realizar o docking molecular de forma escalável e eficiente. Com Docker, as dependências e ferramentas necessárias, incluindo MGLTools, Open Babel e AutoDock-GPU, são encapsuladas em containers, facilitando a implantação e garantindo a consistência do ambiente de execução.

### Docker Configuration

O projeto contém dois Dockerfiles principais:

1. **DockerFile.Worker:** Este arquivo Docker configura o ambiente necessário para executar o worker do Celery, que inclui a instalação do MGLTools, Open Babel e AutoDock-GPU. Este container é responsável por processar as tarefas de docking em fila, utilizando o poder de processamento da GPU, quando disponível.

2. **DockerFile:** Configura o ambiente para executar o servidor Django, que gerencia a interface web do projeto e a API para submissão e monitoramento das tarefas de docking.

### Utilização do Celery e RabbitMQ

O Celery é um sistema de fila de tarefas distribuídas, usado para processar as tarefas de docking de forma assíncrona e escalável. No PlasmoDocking, o Celery é configurado para trabalhar com o RabbitMQ como broker de mensagens, gerenciando a distribuição de tarefas entre os workers disponíveis.

**Celery:** Permite a execução paralela e distribuída das simulações de docking, melhorando significativamente a eficiência e velocidade do processamento, especialmente em conjunto com a execução em GPUs.

**RabbitMQ:** Atua como intermediário entre o servidor Django e os workers do Celery, enfileirando as tarefas de docking enviadas através da interface web ou API e distribuindo-as para os workers processarem.

## Início Rápido

Para iniciar o processo de PlasmoDocking, você precisa ter um arquivo `.sdf` contendo os ligantes de interesse (atualmente é permitido no maximo 10 ligantes no `.sdf` para o processo). O sistema automatizado irá processar este arquivo através de várias etapas para identificar as melhores energias de ligação com os receptores disponíveis.

## Utilização das Ferramentas

### MGLTools

MGLTools é uma suíte de software que fornece ferramentas para visualização, análise e preparação de moléculas para simulações de docking. No Projeto PlasmoDocking, o MGLTools é utilizado principalmente para a conversão dos ligantes do formato `.pdb` para `.pdbqt`, preparando-os para o processo de docking com o AutoDock-GPU. Esta etapa é crucial para definir os átomos ativos dos ligantes e possíveis flexibilidades das moléculas.

**Passos para Preparação dos Ligantes:**

1. **Conversão de Formatos:** Os ligantes separados do arquivo `.sdf` são convertidos para `.pdb` utilizando o Open Babel.
2. **Preparação para Docking:** Usando o script `prepare_ligand4.py` do MGLTools, os ligantes no formato `.pdb` são processados para gerar os arquivos `.pdbqt`, que contêm informações sobre cargas atômicas, tipos de átomos e potenciais pontos de flexão das moléculas.

### Open Babel

Open Babel é uma ferramenta de química computacional usada para converter dados de moléculas entre diferentes formatos de arquivo. No projeto, Open Babel é utilizado para duas tarefas principais:

1. **Split de Ligantes:** A partir do arquivo `.sdf` fornecido, Open Babel separa os ligantes individuais para serem processados independentemente.
2. **Conversão de Formatos:** Transforma os ligantes de `.sdf` para `.pdb`, e posteriormente, converte os resultados do docking de `.pdbqt` para `.pdb`, facilitando a visualização e análise.

### AutoDock-GPU

AutoDock-GPU é uma versão otimizada do AutoDock, um dos softwares mais utilizados para docking molecular, que aproveita o poder de processamento das GPUs para acelerar significativamente os cálculos. No PlasmoDocking, AutoDock-GPU é responsável por executar o docking dos ligantes preparados contra os receptores selecionados, calculando as energias de ligação e determinando a melhor conformação para cada par ligante-receptor.

**Execução do Docking:**

1. **Preparação dos Receptores:** Os receptores são preparados anteriormente e armazenados no banco de dados, incluindo a geração de mapas de grid necessários para o docking.
2. **Docking Automatizado:** Para cada par ligante-receptor, o AutoDock-GPU é executado, utilizando os arquivos `.pdbqt` dos ligantes e os mapas de grid dos receptores para simular o docking. Este processo é realizado em paralelo para todos os ligantes contra todos os receptores disponíveis.
3. **Análise dos Resultados:** Após a execução do docking, as melhores energias de ligação são extraídas, permitindo identificar as interações mais promissoras.

Essas ferramentas, juntas, formam a espinha dorsal do processo de PlasmoDocking, permitindo a análise em larga escala das potenciais interações ligante-receptor com eficiência e precisão.

## Processo PlasmoDocking: Fluxograma Detalhado

### 1. Recebimento do Arquivo `.sdf`

O processo começa com o usuário fornecendo um arquivo `.sdf` contendo várias estruturas de ligantes.

### 2. Criação de Diretórios

Baseado no nome do usuário e do processo, diretórios específicos são criados para armazenar macromoléculas (receptores), ligantes, resultados de docking, entre outros arquivos necessários.

### 3. Split dos Ligantes do `.sdf`

O arquivo `.sdf` é dividido para separar os ligantes individuais, utilizando ferramentas como o Open Babel.

### 4. Preparação dos Ligantes: `.sdf` para `.pdb`

Os ligantes separados são convertidos do formato `.sdf` para `.pdb`, facilitando manipulações subsequentes.

### 5. Preparação dos Ligantes para `.pdbqt`

Utilizando o MGLTools, os ligantes no formato `.pdb` são preparados para o formato `.pdbqt`, adequado para o processo de docking.

### 6. Consulta dos Receptores no Banco de Dados

Todos os receptores disponíveis no banco de dados (aproximadamente 39) são selecionados para participar do processo de docking.

### 7. Execução do Docking

Para cada par ligante-receptor, o AutoDock-GPU é utilizado para executar o docking, explorando conformações e calculando energias de ligação.

**Exemplo:** Um arquivo `.sdf` com 10 ligantes enviado para o processo. Cada ligante será executado o processo para cada receptor. Ao total neste exemplo serão excutados 390 processos de docagem molecular com o AutodockGPU com o parametro de --nrun 50 (cada processo de docagem molecular é executado 50 vezes).

### 8. Análise dos Resultados

Dos resultados de docking, extrai-se a melhor energia de ligação para cada par receptor-ligante, permitindo identificar as interações mais promissoras.

### 9. Organização dos Resultados

Os resultados são organizados em diretórios específicos e também compilados em um arquivo JSON e um arquivo CSV, facilitando análises subsequentes.

### 10. Dashboard Interativo e Visualização 3D

A aplicação frontend acessível em "www.plasmodocking-labioquim.unir.br" oferece um dashboard interativo para análise dos resultados. Através deste dashboard, os usuários podem visualizar os dados em diferentes formatos, incluindo tabelas e gráficos, facilitando a interpretação dos resultados. Além disso, é possível visualizar as estruturas dos complexos ligante-receptor em 3D utilizando o NGL Viewer, proporcionando uma compreensão mais aprofundada das interações moleculares.

## Conclusão

O Projeto PlasmoDocking representa uma ferramenta valiosa para pesquisadores em bioquímica e farmacologia, simplificando o processo de identificação de ligantes promissores para uma vasta gama de receptores. A automação e a eficiência do processo permitem uma análise em larga escala, acelerando potencialmente a descoberta de novos candidatos a fármacos.