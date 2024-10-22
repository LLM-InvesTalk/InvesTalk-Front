import { AreaPlot, lineElementClasses } from "@mui/x-charts/LineChart";
import { areaElementClasses } from "@mui/x-charts/LineChart";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ResponsiveChartContainer } from "@mui/x-charts/ResponsiveChartContainer";
import { useEffect, useState } from "react";
import axios from "axios";

const StockInfoChart = (props) => {
  const { tickerSymbol, period, setPercentageChange } = props;
  const [data, setData] = useState(null);

  useEffect(() => {
    axios
      .get(`http://localhost:5000/api/stockinfochart/${tickerSymbol}/${period}`)
      .then((response) => {
        console.log(response); // 데이터 확인을 위해 로그 출력
        setData(response.data);
        setPercentageChange(response.data.percentage_change);
      })
      .catch((error) => console.error("Error fetching data:", error));
  }, [tickerSymbol, period]);

  const config = {
    dataset: data ? data.data : [], // 데이터가 없을 때 빈 배열로 처리
    xAxis: [
      {
        dataKey: "x",
      },
    ],
    series: [
      {
        type: "line",
        curve: "natural",
        dataKey: "y",
        showMark: false,
        area: true,
        color: "#D2A5FF",
      },
    ],
    width: 300,
    height: 100,
    margin: { top: 25, bottom: 50, left: 50, right: 30 },
    sx: {
      [`& .${areaElementClasses.root}`]: {
        fill: "url(#swich-color-id-1)",
      },
      [`& .${lineElementClasses.root}`]: {
        strokeWidth: 1,
      },
    },
  };

  function ColorSwich({ id }) {
    return (
      <defs>
        <linearGradient id={id} x2="0" y2="1" gradientUnits="objectBoundingBox">
          <stop offset="5%" stopColor="rgb(225, 247, 255)" />
          <stop offset="30%" stopColor="rgb(236, 255, 248)" />
          <stop offset="100%" stopColor="rgb(247, 239, 255)" />
        </linearGradient>
      </defs>
    );
  }

  return (
    <div>
      {data ? (
        <ResponsiveChartContainer {...config}>
          <LinePlot />
          <AreaPlot />
          <ColorSwich id="swich-color-id-1" />
        </ResponsiveChartContainer>
      ) : (
        <p>Loading data...</p> // 데이터 로딩 중 메시지
      )}
    </div>
  );
};

export default StockInfoChart;
