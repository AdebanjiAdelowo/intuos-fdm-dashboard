import {
  Table, TableHead, TableHeaderCell, TableBody, TableRow, TableCell,
} from '@tremor/react'

interface Column {
  key: string
  label: string
  render?: (value: unknown, row: Record<string, unknown>) => React.ReactNode
}

interface Props {
  columns: Column[]
  data: Record<string, unknown>[]
  onRowClick?: (row: Record<string, unknown>) => void
  emptyMessage?: string
}

export default function DataTable({ columns, data, onRowClick, emptyMessage = 'No data' }: Props) {
  if (data.length === 0) {
    return <div className="text-center py-12 text-tremor-content text-sm">{emptyMessage}</div>
  }

  return (
    <Table>
      <TableHead>
        <TableRow>
          {columns.map((col) => (
            <TableHeaderCell key={col.key}>{col.label}</TableHeaderCell>
          ))}
        </TableRow>
      </TableHead>
      <TableBody>
        {data.map((row, i) => (
          <TableRow
            key={i}
            onClick={() => onRowClick?.(row)}
            className={onRowClick ? 'cursor-pointer hover:bg-tremor-background-muted transition-colors' : ''}
          >
            {columns.map((col) => (
              <TableCell key={col.key}>
                {col.render ? col.render(row[col.key], row) : String(row[col.key] ?? '—')}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
