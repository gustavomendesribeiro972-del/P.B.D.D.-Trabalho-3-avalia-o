--Logins / Cadastros

CREATE TABLE public.perfil(
  id_perfil SERIAL PRIMARY KEY,
  nome_usuario VARCHAR(30) UNIQUE NOT NULL,
  email VARCHAR(254) UNIQUE NOT NULL,
  criado_em TIMESTAMP DEFAULT now()
);

CREATE TABLE public.empresa(
  id_empresa SERIAL PRIMARY KEY,
  nomefantasia_empresa VARCHAR(55) NOT NULL,
  cnpj_empresa VARCHAR(14) UNIQUE NOT NULL,
  descricao_empresa VARCHAR(440) DEFAULT 'Uma empresa registrada no CentroMercados',
  email VARCHAR(254) UNIQUE NOT NULL,
  telefone VARCHAR(20),
  criado_em TIMESTAMP DEFAULT now()
);

CREATE TABLE public.empresa_perfil(
  empresa_id INTEGER NOT NULL,
  perfil_id INTEGER NOT NULL,

  PRIMARY KEY (empresa_id, perfil_id),

  CONSTRAINT fk_perfil_id
    FOREIGN KEY (perfil_id)
    REFERENCES perfil(id_perfil),

  CONSTRAINT fk_empresa_id
    FOREIGN KEY (empresa_id)
    REFERENCES empresa(id_empresa)
)