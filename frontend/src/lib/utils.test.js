import test from 'node:test'
import assert from 'node:assert'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

function cn(...inputs) {
  return twMerge(clsx(inputs))
}

test('cn utility combines class names properly', () => {
  const result = cn('bg-red-500', 'text-white', false && 'hidden', 'p-4')
  assert.strictEqual(result, 'bg-red-500 text-white p-4')
})

test('cn utility resolves tailwind conflicts correctly', () => {
  const result = cn('p-2', 'p-4', 'bg-red-500', 'bg-blue-500')
  assert.strictEqual(result, 'p-4 bg-blue-500')
})

test('cn handles conditional objects and arrays', () => {
  const result = cn(['font-bold', { 'text-center': true, 'opacity-0': false }])
  assert.strictEqual(result, 'font-bold text-center')
})
