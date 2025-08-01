import sys

class CutOptimizer:
    def __init__(self, material_length, pieces, kerf=0, stock=500):
        self.material_length = material_length
        self.kerf = kerf
        self.stock = stock
        self.piece_counts = self._normalize_pieces(pieces)
        self.bars = []

    def _normalize_pieces(self, pieces):
        piece_counts = {}
        if not pieces or not isinstance(pieces, list):
            raise ValueError("Lista de peças inválida.")

        for p in pieces:
            if isinstance(p, int):
                piece_counts[p] = piece_counts.get(p, 0) + 1
            elif isinstance(p, (list, tuple)) and len(p) == 2:
                length, qty = p
                piece_counts[length] = piece_counts.get(length, 0) + qty
            else:
                raise ValueError(f"Formato de peça inválido: {p}")
        
        print(f"Peças únicas: {list(piece_counts.keys())}", file=sys.stderr)
        return piece_counts

    def optimize(self):
        all_pieces = []
        for length, qty in self.piece_counts.items():
            all_pieces.extend([length] * qty)

        all_pieces.sort(reverse=True)
        bars = []

        for piece in all_pieces:
            placed = False
            for bar in bars:
                total_length = sum(bar['pieces']) + (len(bar['pieces']) - 1) * self.kerf
                if total_length + piece + self.kerf <= self.material_length:
                    bar['pieces'].append(piece)
                    placed = True
                    break
            if not placed:
                bars.append({'pieces': [piece], 'remaining': self.material_length - piece})

        for bar in bars:
            used_length = sum(bar['pieces']) + (len(bar['pieces']) - 1) * self.kerf
            bar['remaining'] = self.material_length - used_length

        formatted_bars = []
        for i, bar in enumerate(bars):
            segmentos = {}
            for piece in bar['pieces']:
                segmentos[piece] = segmentos.get(piece, 0) + 1
            detalhes = " | ".join([f"Segmento {idx+1} - {length} x {qty}"
                                   for idx, (length, qty) in enumerate(segmentos.items())])
            formatted = f"// {self.material_length}mm / Barra {i+1} | {detalhes} | Desperdício - {bar['remaining']}mm"
            formatted_bars.append(formatted)

        total_used = sum(sum(bar['pieces']) + (len(bar['pieces']) - 1) * self.kerf for bar in bars)
        total_cuts = sum(len(bar['pieces']) for bar in bars)
        total_requested = sum(self.piece_counts.values())
        efficiency = (total_used / (len(bars) * self.material_length)) * 100 if bars else 0
        total_waste = sum(bar['remaining'] for bar in bars)

        print(f"Barras otimizadas: {bars}", file=sys.stderr)
        print(f"Resumo - Material total: {len(bars) * self.material_length}mm, Barras necessárias: {len(bars)}, "
              f"Material usado: {total_used}mm, Desperdício total: {total_waste}mm, "
              f"Total de cortes: {total_requested}, Eficiência: {efficiency:.1f}%", file=sys.stderr)

        return {
            'bars': bars,
            'formatted_bars': formatted_bars,
            'material_total': len(bars) * self.material_length,
            'bars_needed': len(bars),
            'material_used': total_used,
            'total_waste': total_waste,
            'total_cuts': total_requested,
            'efficiency': efficiency
        }


def optimize_cuts(material_length, pieces, kerf=0, stock=500):
    print(f"Iniciando otimização com material_length={material_length}, pieces={pieces}, kerf={kerf}, stock={stock}", file=sys.stderr)
    optimizer = CutOptimizer(material_length, pieces, kerf, stock)
    result = optimizer.optimize()
    print(f"Resultado da otimização: {result}", file=sys.stderr)
    return result
