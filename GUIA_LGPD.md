# Guia de privacidade do sistema

Este guia liga as telas às funções e tabelas para facilitar a manutenção. O
software oferece controles técnicos ao Controlador (a oficina); isso não prova,
por si só, conformidade legal. Finalidades, bases legais, prazos e respostas a
solicitações continuam sendo decisões e deveres do Controlador.

## Fluxo de acesso

1. `main.py` valida usuário e senha na tabela `usuarios`.
2. `config.py` deriva e verifica hashes PBKDF2-SHA256. Senhas antigas em texto
   puro são migradas para hash assim que o login correto ocorre.
3. A credencial inicial `admin/admin` é recusada até que uma senha nova com no
   mínimo 12 caracteres seja criada.
4. `modulo_lgpd.py:exigir_aceite_termos` confere a versão dos termos. Se não
   houver aceite, a janela modal bloqueia o menu. O registro vai para
   `termos_aceites_log` com usuário, horário, versão e IP local disponível.
5. Interações de teclado e mouse em `main.py` reiniciam o timeout de 15 minutos.
   O logout limpa a identidade e o nível de acesso mantidos em memória.

## Cadastro e painel do titular

- `modulo_financeiro.py:mostrar_tela_clientes` apresenta dois opt-ins
  promocionais independentes. `IntVar(value=0)` deixa os dois desmarcados em
  novos cadastros; salvar grava a escolha e a data em `clientes`.
- A lista geral de clientes usa `modulo_lgpd.py:mascarar_documento`. A busca e
  a tabela do painel LGPD também exibem documento mascarado por padrão.
- `main.py` registra a aba Privacidade / LGPD e abre
  `modulo_lgpd.py:mostrar_painel_lgpd`.
- A exportação CSV junta cadastro, orçamentos e novas ordens por `codigo_cliente`.
  Para ordens antigas, sem esse vínculo, usa o nome enquanto ainda existe no
  cadastro. O CSV contém dados pessoais e deve ser entregue por canal seguro.
- A revelação do documento é registrada em `lgpd_eventos` e só é permitida
  para `nivel` igual a `admin` ou `gerente`. O administrador inicial recebe
  `admin`; outros usuários recebem `operador` por padrão.

## Anonimização e histórico

`modulo_lgpd.py:anonimizar_cliente` confirma o código digitado e executa as
alterações numa única transação. Mantém o código interno e os valores financeiros,
substitui dados cadastrais por marcadores ou nulos e desmarca os opt-ins. Também
limpa campos conhecidos de `orcamentos`, substitui referências conhecidas em
`uso` e remove nome/identificadores do histórico `atualizacoes`. O resultado é
registrado em `lgpd_eventos` sem duplicar o nome ou documento.

Não se apagam colunas arbitrárias de texto livre, notas fiscais, PDFs, planilhas,
backups ou arquivos já exportados fora do banco. Esses locais precisam entrar no
inventário de dados e no procedimento operacional da oficina. Valide cada caso
de anonimização e as obrigações de guarda antes de executá-la; ela é irreversível.

## Tabelas e manutenção

- `clientes`: cadastro operacional, consentimentos promocionais e data da última
  atualização do consentimento.
- `termos_aceites_log`: trilha de aceite por versão do documento.
- `lgpd_eventos`: exportação, revelação/ocultação e anonimização.
- `usuarios.nivel`: autorização usada para revelar documentos.

`config.py` cria as tabelas e migra colunas antigas tanto no SQLite quanto no
PostgreSQL. `PLACEHOLDER_SQL` escolhe o marcador de parâmetros para as consultas
novas que precisam funcionar nos dois bancos.

## Pendências antes de produção

- **Retenção de contas canceladas:** este aplicativo é uma instalação de uma
  oficina por banco e não possui cadastro de empresas/tenants, data de
  cancelamento ou estados de encerramento. Por isso não existe um critério
  confiável para um job apagar dados após cinco anos; executar uma limpeza
  automática agora poderia apagar uma empresa ativa. Para fazer isso, primeiro
  modele o ciclo de vida da empresa e valide os prazos aplicáveis. Em Windows,
  o agendamento seria feito pelo Agendador de Tarefas, não por cron.
- **Criptografia em repouso:** o SQLite continua sendo um arquivo sem criptografia
  de banco. Hash de senha não criptografa documentos ou outros campos. Habilite
  criptografia integral do dispositivo/volume (por exemplo, BitLocker) e defina
  gestão e rotação de chaves para bancos remotos antes de armazenar dados de alto
  risco. Não grave uma chave junto ao banco ou dentro do executável.
- **IP:** por ser um programa desktop sem API web, o log registra o IP local que
  o computador informa; ele não é necessariamente o IP público do usuário.
- **Textos legais:** a versão inicial exibida no primeiro acesso é um rascunho
  operacional. Revise Termos de Uso e Política de Privacidade para a operação
  real, os canais de suporte, retenção e bases legais antes de usá-los como
  instrumento jurídico.