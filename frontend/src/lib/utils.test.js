import test from 'node:test'
import assert from 'node:assert'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { wrapSelection } from '../utils/textFormatter.ts'

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

test('wrapSelection wraps text with bold tags correctly', () => {
  const fullText = 'سلام به تفکر'
  // 'سلام ' is 5 chars, 'به تفکر' is 7 chars (5..12)
  const result = wrapSelection(fullText, 5, 12, 'bold')
  assert.strictEqual(result.newText, 'سلام **به تفکر**')
  assert.strictEqual(result.newCursorStart, 7)
  assert.strictEqual(result.newCursorEnd, 14)
})

test('wrapSelection toggles off bold when already enclosed', () => {
  const fullText = 'سلام **به تفکر** خوش آمدید'
  // '**به تفکر**' is 11 chars (5..16)
  const result = wrapSelection(fullText, 5, 16, 'bold')
  assert.strictEqual(result.newText, 'سلام به تفکر خوش آمدید')
  assert.strictEqual(result.newCursorStart, 5)
  assert.strictEqual(result.newCursorEnd, 12)
})

test('wrapSelection toggles off bold when selected inside wrapper tags', () => {
  const fullText = 'سلام **به تفکر** خوش آمدید'
  // 'به تفکر' is 7 chars (7..14) inside '**' and '**'
  const result = wrapSelection(fullText, 7, 14, 'bold')
  assert.strictEqual(result.newText, 'سلام به تفکر خوش آمدید')
  assert.strictEqual(result.newCursorStart, 5)
  assert.strictEqual(result.newCursorEnd, 12)
})

test('wrapSelection quote wrapping and toggling off', () => {
  const fullText = 'سطر اول پیام'
  const quoted = wrapSelection(fullText, 0, fullText.length, 'quote')
  assert.strictEqual(quoted.newText, '> سطر اول پیام')

  const unquoted = wrapSelection(quoted.newText, 0, quoted.newText.length, 'quote')
  assert.strictEqual(unquoted.newText, 'سطر اول پیام')
})
