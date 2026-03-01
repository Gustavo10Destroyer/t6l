# Overview
Para usar a ferramenta, você precisa ter o Python instalado.<br>

> [!IMPORTANT]
> Esta ferramenta é feita para uso no Windows e pode não funcionar devidamente em outros sistemas.

# How To
### Baixar e instalar a ferramenta.
1. Baixe o código da ferramenta ou clone o repositório.
2. Na pasta da ferramenta, [instale as dependências](#instalar-dependências).
3. Logo após, [configure a ferramenta no seu ambiente](#configurar-ferramenta).

### Instalar dependências
```ps
python -m pip install -r requirements.txt
```
Esse comando vai configurar a ferramenta no seu ambiente, a partir de então, você pode usá-la em qualquer lugar executando o comando `t6l`.

### Configurar ferramenta
```ps
python main.py setup
```
Esse comando vai configurar a ferramenta no seu ambiente, a partir de então, você pode usá-la em qualquer lugar executando o comando `t6l`.

### Remover a ferramenta do ambiente.
```ps
t6l setup --remove
```
Esse comando vai remover a ferramenta do seu ambiente, a partir daí você pode apagar a pasta da mesma.