import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface LossChartProps {
  data: { step: number; loss: number }[]
}

export default function LossChart({ data }: LossChartProps) {
  if (!data.length) {
    return (
      <div className="h-48 flex items-center justify-center text-gray-500 text-sm">
        No training data yet
      </div>
    )
  }

  return (
    <div className="h-48">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey="step" stroke="#666" fontSize={11} />
          <YAxis stroke="#666" fontSize={11} />
          <Tooltip
            contentStyle={{ backgroundColor: '#1e1e1e', border: '1px solid #333', borderRadius: 6 }}
            labelStyle={{ color: '#999' }}
            itemStyle={{ color: '#00ff88' }}
          />
          <Line
            type="monotone"
            dataKey="loss"
            stroke="#00ff88"
            strokeWidth={2}
            dot={false}
            animationDuration={300}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
