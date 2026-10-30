export interface FonteLegal {
  lei: string | null
  titulo: string | null
  capitulo: string | null
  secao: string | null
  artigo: string | null
  trecho: string
}

export interface RespostaChat {
  resposta: string
  fontes: FonteLegal[]
}

export interface StatusProntidao {
  status: 'pronto' | 'indisponivel'
  banco_vetorial: boolean
}

export type TipoErroApi =
  | 'validacao'
  | 'limite'
  | 'indisponivel'
  | 'rede'
  | 'tempo_esgotado'
  | 'desconhecido'

