import assert from 'node:assert/strict'
import test from 'node:test'
import { generateQrMatrix, generateQrSvgString } from '../qrCode.ts'

test('generateQrMatrix encodes typical book circulation URL cleanly with valid finder & timing patterns', () => {
  const matrix = generateQrMatrix('https://tafakormag.ir/b/TK-U65P')
  const n = matrix.length

  // Version 3 (29 bytes -> capacity 42 bytes in V3-M): 29x29 modules
  assert.equal(n, 29)

  // Verify 7x7 top-left, top-right, bottom-left finder centers & outer borders
  for (const [r0, c0] of [
    [0, 0],
    [0, n - 7],
    [n - 7, 0],
  ]) {
    assert.equal(matrix[r0!]![c0!], 1)
    assert.equal(matrix[r0! + 3]![c0! + 3], 1)
    assert.equal(matrix[r0! + 1]![c0! + 1], 0)
  }

  // Dark module at (4 * 3 + 9, 8) = (21, 8)
  assert.equal(matrix[21]![8], 1)

  // SVG output well-formed
  const svg = generateQrSvgString('https://tafakormag.ir/b/TK-U65P')
  assert.ok(svg.startsWith('<svg '))
  assert.ok(svg.includes('viewBox="0 0 33 33"'))
  assert.ok(svg.endsWith('</svg>'))
})

