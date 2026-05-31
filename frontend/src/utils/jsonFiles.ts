export const safeJsonFilename = (name: string, suffix: string) => {
  const safeName = name.replace(/[^\wа-яА-ЯёЁ.-]+/g, "_").slice(0, 80)
  return `${safeName || "export"}.${suffix}.json`
}

export const downloadJson = (data: unknown, filename: string) => {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export const readJsonFile = async <T>(file: File): Promise<T> => {
  const text = await file.text()
  return JSON.parse(text) as T
}
