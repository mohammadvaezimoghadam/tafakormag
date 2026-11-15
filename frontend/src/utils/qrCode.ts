/**
 * Minimal standards-compliant ISO/IEC 18004 QR Code matrix & SVG generator
 * supporting Byte mode (UTF-8) and Error Correction Level M (Versions 1-6).
 * Pure TypeScript with zero runtime dependencies.
 */

interface VersionSpec {
  version: number
  size: number
  totalDataCodewords: number
  ecCodewordsPerBlock: number
  blocks: number
  remainderBits: number
  alignments: number[]
}

const VERSION_SPECS_M: VersionSpec[] = [
  { version: 1, size: 21, totalDataCodewords: 16, ecCodewordsPerBlock: 10, blocks: 1, remainderBits: 0, alignments: [] },
  { version: 2, size: 25, totalDataCodewords: 28, ecCodewordsPerBlock: 16, blocks: 1, remainderBits: 7, alignments: [6, 18] },
  { version: 3, size: 29, totalDataCodewords: 44, ecCodewordsPerBlock: 26, blocks: 1, remainderBits: 7, alignments: [6, 22] },
  { version: 4, size: 33, totalDataCodewords: 64, ecCodewordsPerBlock: 18, blocks: 2, remainderBits: 7, alignments: [6, 26] },
  { version: 5, size: 37, totalDataCodewords: 86, ecCodewordsPerBlock: 24, blocks: 2, remainderBits: 7, alignments: [6, 30] },
  { version: 6, size: 41, totalDataCodewords: 108, ecCodewordsPerBlock: 16, blocks: 4, remainderBits: 7, alignments: [6, 34] },
]

// GF(256) log / exp tables with primitive polynomial x^8 + x^4 + x^3 + x^2 + 1 (0x11D)
const GF_EXP = new Uint8Array(512)
const GF_LOG = new Uint8Array(256)

for (let i = 0, x = 1; i < 255; i++) {
  GF_EXP[i] = x
  GF_LOG[x] = i
  x <<= 1
  if (x & 0x100) x ^= 0x11d
}
for (let i = 255; i < 512; i++) {
  GF_EXP[i] = GF_EXP[i - 255]!
}

function gfMul(a: number, b: number): number {
  if (a === 0 || b === 0) return 0
  return GF_EXP[GF_LOG[a]! + GF_LOG[b]!]!
}

function buildGeneratorPoly(degree: number): number[] {
  let poly = [1]
  for (let i = 0; i < degree; i++) {
    const next = new Array<number>(poly.length + 1).fill(0)
    const factor = GF_EXP[i]!
    for (let j = 0; j < poly.length; j++) {
      next[j] = (next[j]! ^ poly[j]!)
      next[j + 1] = (next[j + 1]! ^ gfMul(poly[j]!, factor))
    }
    poly = next
  }
  return poly
}

function computeEcCodewords(data: number[], ecLen: number): number[] {
  const gen = buildGeneratorPoly(ecLen)
  const buffer = new Array<number>(data.length + ecLen).fill(0)
  for (let i = 0; i < data.length; i++) buffer[i] = data[i]!

  for (let i = 0; i < data.length; i++) {
    const coef = buffer[i]!
    if (coef === 0) continue
    for (let j = 0; j < gen.length; j++) {
      buffer[i + j] = buffer[i + j]! ^ gfMul(gen[j]!, coef)
    }
  }
  return buffer.slice(data.length)
}

function appendBits(out: number[], value: number, bitLen: number): void {
  for (let i = bitLen - 1; i >= 0; i--) {
    out.push((value >>> i) & 1)
  }
}

function encodeDataCodewords(bytes: Uint8Array, totalDataCodewords: number): number[] {
  const bits: number[] = []
  // Byte mode indicator (0100) + 8-bit char count (valid for Versions 1..9)
  appendBits(bits, 0b0100, 4)
  appendBits(bits, bytes.length, 8)
  for (const b of bytes) {
    appendBits(bits, b, 8)
  }

  const maxBits = totalDataCodewords * 8
  const terminatorLen = Math.min(4, maxBits - bits.length)
  appendBits(bits, 0, terminatorLen)

  while (bits.length % 8 !== 0) bits.push(0)

  const codewords: number[] = []
  for (let i = 0; i < bits.length; i += 8) {
    let val = 0
    for (let b = 0; b < 8; b++) {
      val = (val << 1) | (bits[i + b] ?? 0)
    }
    codewords.push(val)
  }

  const padBytes = [0xec, 0x11]
  let padIdx = 0
  while (codewords.length < totalDataCodewords) {
    codewords.push(padBytes[padIdx % 2]!)
    padIdx++
  }
  return codewords
}

function buildFinalBitStream(bytes: Uint8Array, spec: VersionSpec): number[] {
  const dataCodewords = encodeDataCodewords(bytes, spec.totalDataCodewords)
  const blockSize = Math.floor(spec.totalDataCodewords / spec.blocks)
  const dataBlocks: number[][] = []
  const ecBlocks: number[][] = []

  let offset = 0
  for (let b = 0; b < spec.blocks; b++) {
    const slice = dataCodewords.slice(offset, offset + blockSize)
    offset += blockSize
    dataBlocks.push(slice)
    ecBlocks.push(computeEcCodewords(slice, spec.ecCodewordsPerBlock))
  }

  const interleaved: number[] = []
  for (let i = 0; i < blockSize; i++) {
    for (let b = 0; b < spec.blocks; b++) {
      interleaved.push(dataBlocks[b]![i]!)
    }
  }
  for (let i = 0; i < spec.ecCodewordsPerBlock; i++) {
    for (let b = 0; b < spec.blocks; b++) {
      interleaved.push(ecBlocks[b]![i]!)
    }
  }

  const bits: number[] = []
  for (const cw of interleaved) appendBits(bits, cw, 8)
  for (let r = 0; r < spec.remainderBits; r++) bits.push(0)
  return bits
}

function computeFormatBits(maskPattern: number): number {
  // EC Level M = 00
  const data = (0b00 << 3) | maskPattern
  let rem = data << 10
  const poly = 0b10100110111
  for (let bit = 14; bit >= 10; bit--) {
    if ((rem >>> bit) & 1) {
      rem ^= poly << (bit - 10)
    }
  }
  return ((data << 10) | rem) ^ 0b101010000010010
}

function placeFinder(grid: number[][], reserved: boolean[][], row: number, col: number): void {
  const size = grid.length
  for (let dr = -1; dr <= 7; dr++) {
    for (let dc = -1; dc <= 7; dc++) {
      const r = row + dr
      const c = col + dc
      if (r < 0 || r >= size || c < 0 || c >= size) continue
      const inOuter = dr >= 0 && dr <= 6 && dc >= 0 && dc <= 6
      const onBorder = dr === 0 || dr === 6 || dc === 0 || dc === 6
      const inInner = dr >= 2 && dr <= 4 && dc >= 2 && dc <= 4
      grid[r]![c] = inOuter && (onBorder || inInner) ? 1 : 0
      reserved[r]![c] = true
    }
  }
}

function placeAlignment(grid: number[][], reserved: boolean[][], centerR: number, centerC: number): void {
  for (let dr = -2; dr <= 2; dr++) {
    for (let dc = -2; dc <= 2; dc++) {
      const r = centerR + dr
      const c = centerC + dc
      const isDark = Math.max(Math.abs(dr), Math.abs(dc)) !== 1
      grid[r]![c] = isDark ? 1 : 0
      reserved[r]![c] = true
    }
  }
}

function shouldMask(mask: number, r: number, c: number): boolean {
  switch (mask) {
    case 0: return (r + c) % 2 === 0
    case 1: return r % 2 === 0
    case 2: return c % 3 === 0
    case 3: return (r + c) % 3 === 0
    case 4: return (Math.floor(r / 2) + Math.floor(c / 3)) % 2 === 0
    case 5: return ((r * c) % 2 + (r * c) % 3) === 0
    case 6: return (((r * c) % 2 + (r * c) % 3) % 2) === 0
    case 7: return (((r + c) % 2 + (r * c) % 3) % 2) === 0
    default: return false
  }
}

function writeFormatInfo(grid: number[][], reserved: boolean[][], formatBits: number): void {
  const size = grid.length
  for (let i = 0; i < 15; i++) {
    const bit = (formatBits >>> i) & 1

    // Vertical strip near top-left & bottom-left
    if (i < 6) {
      grid[i]![8] = bit
      reserved[i]![8] = true
    } else if (i < 8) {
      grid[i + 1]![8] = bit
      reserved[i + 1]![8] = true
    } else {
      grid[size - 15 + i]![8] = bit
      reserved[size - 15 + i]![8] = true
    }

    // Horizontal strip near top-right & top-left
    if (i < 8) {
      grid[8]![size - i - 1] = bit
      reserved[8]![size - i - 1] = true
    } else if (i < 9) {
      grid[8]![15 - i] = bit
      reserved[8]![15 - i] = true
    } else {
      grid[8]![15 - i - 1] = bit
      reserved[8]![15 - i - 1] = true
    }
  }
}

function computePenalty(grid: number[][]): number {
  const n = grid.length
  let score = 0

  // Rule 1: 5+ same-color runs horizontally & vertically
  for (let r = 0; r < n; r++) {
    let runH = 1
    let runV = 1
    for (let i = 1; i < n; i++) {
      if (grid[r]![i] === grid[r]![i - 1]) runH++
      else {
        if (runH >= 5) score += 3 + (runH - 5)
        runH = 1
      }
      if (grid[i]![r] === grid[i - 1]![r]) runV++
      else {
        if (runV >= 5) score += 3 + (runV - 5)
        runV = 1
      }
    }
    if (runH >= 5) score += 3 + (runH - 5)
    if (runV >= 5) score += 3 + (runV - 5)
  }

  // Rule 2: 2x2 same-color blocks
  for (let r = 0; r < n - 1; r++) {
    for (let c = 0; c < n - 1; c++) {
      const v = grid[r]![c]
      if (v === grid[r]![c + 1] && v === grid[r + 1]![c] && v === grid[r + 1]![c + 1]) {
        score += 3
      }
    }
  }

  // Rule 3: 1:1:3:1:1 finder-like patterns
  const p1 = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0]
  const p2 = [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1]
  for (let r = 0; r < n; r++) {
    for (let c = 0; c <= n - 11; c++) {
      let mh1 = true
      let mh2 = true
      let mv1 = true
      let mv2 = true
      for (let k = 0; k < 11; k++) {
        if (grid[r]![c + k] !== p1[k]) mh1 = false
        if (grid[r]![c + k] !== p2[k]) mh2 = false
        if (grid[c + k]![r] !== p1[k]) mv1 = false
        if (grid[c + k]![r] !== p2[k]) mv2 = false
      }
      if (mh1 || mh2) score += 40
      if (mv1 || mv2) score += 40
    }
  }

  // Rule 4: dark ratio deviation from 50%
  let dark = 0
  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      if (grid[r]![c] === 1) dark++
    }
  }
  const pct = (dark * 100) / (n * n)
  score += Math.floor(Math.abs(pct - 50) / 5) * 10

  return score
}

export function generateQrMatrix(text: string): number[][] {
  const bytes = new TextEncoder().encode(text)
  const spec = VERSION_SPECS_M.find((s) => bytes.length <= s.totalDataCodewords - 2)
  if (!spec) {
    throw new Error('QR payload too long for Versions 1-6 (Level M)')
  }

  const size = spec.size
  const baseGrid = Array.from({ length: size }, () => new Array<number>(size).fill(0))
  const reserved = Array.from({ length: size }, () => new Array<boolean>(size).fill(false))

  // Finder patterns + separators
  placeFinder(baseGrid, reserved, 0, 0)
  placeFinder(baseGrid, reserved, 0, size - 7)
  placeFinder(baseGrid, reserved, size - 7, 0)

  // Timing patterns
  for (let i = 8; i < size - 8; i++) {
    const bit = i % 2 === 0 ? 1 : 0
    baseGrid[6]![i] = bit
    reserved[6]![i] = true
    baseGrid[i]![6] = bit
    reserved[i]![6] = true
  }

  // Alignment patterns (skip corners overlapping finders)
  for (const ar of spec.alignments) {
    for (const ac of spec.alignments) {
      if (reserved[ar]![ac]) continue
      placeAlignment(baseGrid, reserved, ar, ac)
    }
  }

  // Dark module + reserve format info strips
  baseGrid[4 * spec.version + 9]![8] = 1
  reserved[4 * spec.version + 9]![8] = true
  writeFormatInfo(baseGrid, reserved, 0)

  // Place data & EC bits in zigzag columns
  const bitStream = buildFinalBitStream(bytes, spec)
  let bitIdx = 0
  let dirUp = true
  for (let col = size - 1; col >= 1; col -= 2) {
    if (col === 6) col-- // Skip vertical timing strip
    for (let step = 0; step < size; step++) {
      const r = dirUp ? size - 1 - step : step
      for (let dx = 0; dx < 2; dx++) {
        const c = col - dx
        if (!reserved[r]![c]) {
          baseGrid[r]![c] = bitIdx < bitStream.length ? bitStream[bitIdx]! : 0
          bitIdx++
        }
      }
    }
    dirUp = !dirUp
  }

  // Evaluate masks 0..7 and pick lowest penalty
  let bestGrid = baseGrid
  let bestScore = Number.POSITIVE_INFINITY

  for (let mask = 0; mask < 8; mask++) {
    const candidate = baseGrid.map((row, r) =>
      row.map((val, c) => (reserved[r]![c] ? val : shouldMask(mask, r, c) ? val ^ 1 : val))
    )
    const fmt = computeFormatBits(mask)
    const tempReserved = reserved.map((row) => [...row])
    writeFormatInfo(candidate, tempReserved, fmt)
    const score = computePenalty(candidate)
    if (score < bestScore) {
      bestScore = score
      bestGrid = candidate
    }
  }

  return bestGrid
}

export function generateQrSvgString(text: string, marginModules = 2): string {
  const matrix = generateQrMatrix(text)
  const dim = matrix.length
  const total = dim + marginModules * 2
  const parts: string[] = []
  for (let r = 0; r < dim; r++) {
    for (let c = 0; c < dim; c++) {
      if (matrix[r]![c] === 1) {
        parts.push(`M${c + marginModules},${r + marginModules}h1v1h-1z`)
      }
    }
  }
  return [
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${total} ${total}" shape-rendering="crispEdges">`,
    `<rect width="${total}" height="${total}" fill="#ffffff"/>`,
    `<path d="${parts.join('')}" fill="#09090b"/>`,
    '</svg>',
  ].join('')
}

export function generateQrDataUrl(text: string, marginModules = 2): string {
  const svg = generateQrSvgString(text, marginModules)
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`
}
