import dynamic from 'next/dynamic';
import React from 'react';

const ReactECharts = dynamic(() => import('echarts-for-react'), { ssr: false });

type Props = {
  option: any;
  style?: React.CSSProperties;
};

export default function EChart({ option, style }: Props) {
  return <ReactECharts option={option} style={style ?? { height: 320, width: '100%' }} />;
}

