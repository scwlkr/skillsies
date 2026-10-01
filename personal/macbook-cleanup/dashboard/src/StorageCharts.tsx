import {PieChart, Pie, Cell, Label, BarChart, Bar, XAxis, YAxis, CartesianGrid} from 'recharts';
import {ChartContainer, ChartTooltip, ChartTooltipContent} from '@/components/ui/chart';
import {Card, CardContent} from '@/components/ui/card';
import {ArrowDownRight, CircleDot} from 'lucide-react';
import {size} from './lib/metrics.mjs';
import type {Session} from './types';
const palette = ['#94c8fa', '#b7a7ec', '#e0ac79', '#7fc3b1', '#dc90b0', '#9bbf83'];
export function StorageCharts({session, projection}: {session: Session; projection: {bytes: number; percent: number; gap: number}}) {
  const c = session.status.capacity_after || session.summary.capacity;
  const rows = (session.scan.storage_categories || []).filter(r => r.allocated_bytes > 0);
  const data = rows.slice(0, 5).map((r, i) => ({...r, fill: palette[i]}));
  if (rows.length > 5) data.push({category: 'Everything else', allocated_bytes: rows.slice(5).reduce((n, r) => n + r.allocated_bytes, 0), fill: palette[5]});
  return <div className="grid grid-cols-1 gap-4 min-[680px]:grid-cols-[1fr_1.25fr_1fr]">
    <Card className="min-w-0 gap-0 border-border bg-card py-5 shadow-none"><CardContent className="px-5">
      <p className="text-sm font-medium">Your disk</p>
      <div className="relative mx-auto max-w-64">
        <ChartContainer config={{used: {label: 'Used', color: '#e6a377'}, free: {label: 'Free', color: '#353e49'}}} className="aspect-square h-48 w-full">
          <PieChart><Pie data={[{name: 'Used', value: c.used_bytes}, {name: 'Free', value: c.free_bytes}]} dataKey="value" nameKey="name" innerRadius={66} outerRadius={85} startAngle={90} endAngle={-270} strokeWidth={0} isAnimationActive={false}>
            <Cell fill="#e6a377"/><Cell fill="#353e49"/><Label content={({viewBox}: any) => <text x={viewBox.cx} y={viewBox.cy} textAnchor="middle"><tspan x={viewBox.cx} dy="-2" fill="#edf0f5" fontSize="30" fontWeight="600">{c.used_percent.toFixed(1)}%</tspan><tspan x={viewBox.cx} dy="23" fill="#9da6b4" fontSize="12">used</tspan></text>}/>
          </Pie><ChartTooltip content={<ChartTooltipContent formatter={(value) => size(Number(value))}/>}/></PieChart>
        </ChartContainer>
      </div>
      <div className="flex justify-between text-xs"><span className="text-muted-foreground">{size(c.used_bytes)} used</span><span>{size(c.free_bytes)} free</span></div>
      <p className="mt-3 text-[11px] text-muted-foreground">{c.source.includes("volume") ? "Measured volume capacity" : "Measured physical capacity"} · {size(c.total_bytes)} total</p>
    </CardContent></Card>
    <Card className="min-w-0 gap-0 border-border bg-card py-5 shadow-none"><CardContent className="px-5">
      <div className="flex items-center justify-between"><p className="text-sm font-medium">Where space is going</p><CircleDot size={15} className="text-muted-foreground"/></div>
      {data.length ? <ChartContainer config={{allocated_bytes: {label: 'Allocated', color: '#94c8fa'}}} className="mt-4 h-48 w-full aspect-auto">
        <BarChart data={data} layout="vertical" margin={{left: 0, right: 10}} barSize={12}>
          <CartesianGrid horizontal={false} stroke="#303741" strokeDasharray="3 4"/>
          <XAxis type="number" hide/><YAxis dataKey="category" type="category" width={128} axisLine={false} tickLine={false} tick={{fontSize: 11}}/>
          <Bar dataKey="allocated_bytes" radius={[0, 4, 4, 0]} isAnimationActive={false}>{data.map(r => <Cell key={r.category} fill={r.fill}/>)}</Bar>
          <ChartTooltip cursor={false} content={<ChartTooltipContent formatter={(value) => size(Number(value))}/>}/>
        </BarChart>
      </ChartContainer> : <div className="flex h-52 items-center text-sm text-muted-foreground">Rerun the scanner to add category totals.</div>}
      <p className="mt-3 text-[11px] leading-relaxed text-muted-foreground">Observed file allocation. Coverage gaps and APFS shared data mean these bars may differ from physical usage.</p>
    </CardContent></Card>
    <Card className="min-w-0 gap-0 border-[#3b4858] bg-[#1d2631] py-5 shadow-none"><CardContent className="flex h-full flex-col px-5">
      <div className="flex items-center justify-between"><p className="text-sm font-medium">Make room for what’s next</p><ArrowDownRight size={18} className="text-primary"/></div>
      <div className="mt-6 text-4xl font-semibold tracking-tight">{size(c.reclaim_needed_bytes)}</div>
      <p className="mt-2 text-sm text-muted-foreground">to reach {c.target_percent}% disk usage</p>
      <div className="relative mt-6 h-2 rounded-full bg-[#353e49]"><div className="h-full rounded-full bg-primary" style={{width: `${Math.min(100, projection.percent)}%`}}/><div className="absolute top-[-4px] h-4 w-px bg-white/80" style={{left: `${c.target_percent}%`}}/></div>
      <div className="mt-3 flex justify-between text-xs"><span className="text-muted-foreground">After your selections</span><span className="font-medium text-primary">~{projection.percent.toFixed(1)}% used</span></div>
      <p className="mt-auto pt-4 text-[11px] leading-relaxed text-muted-foreground">{projection.bytes ? `${size(projection.bytes)} selected · ${size(projection.gap)} estimated gap remaining.` : 'Choose items below to explore the impact.'} Actual space recovery is measured after cleanup.</p>
    </CardContent></Card>
  </div>;
}
