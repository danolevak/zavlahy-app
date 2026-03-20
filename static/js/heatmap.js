//  **------heatma js**

function generateData(count, yRange) {
  let i = 0;
  let series = [];
  while (i < count) {
    let x = (i + 1).toString();
    let y = Math.floor(Math.random() * (yRange.max - yRange.min + 1)) + yRange.min;

    series.push({
      x: x,
      y: y
    });
    i++;
  }
  return series;
}
const heatmap1ChartOptions = {
  series: [{
    name: 'Metric1',
    data: generateData(18, {
      min: 0,
      max: 90
    })
  },
    {
      name: 'Metric2',
      data: generateData(18, {
        min: 0,
        max: 90
      })
    },
    {
      name: 'Metric3',
      data: generateData(18, {
        min: 0,
        max: 90
      })
    },
    {
      name: 'Metric4',
      data: generateData(18, {
        min: 0,
        max: 90
      })
    },
    {
      name: 'Metric5',
      data: generateData(18, {
        min: 0,
        max: 90
      })
    },
    {
      name: 'Metric6',
      data: generateData(18, {
        min: 0,
        max: 90
      })
    },
    {
      name: 'Metric7',
      data: generateData(18, {
        min: 0,
        max: 90
      })
    },
    {
      name: 'Metric8',
      data: generateData(18, {
        min: 0,
        max: 90
      })
    },
    {
      name: 'Metric9',
      data: generateData(18, {
        min: 0,
        max: 90
      })
    }
  ],
  chart: {
    fontFamily: "Rubik, serif",
    height: 350,
    type: 'heatmap',
  },
  dataLabels: {
    enabled: false
  },
  colors: [getLocalStorageItem('color-primary','#0F626A'),getLocalStorageItem('color-secondary','#626262'),"#0AB964","#E14E5A","#F9C123","#4196FA","#C8B9D2","#28232D"],
  title: {
    text: ''
  },
  xaxis: {
    labels:{
      style: {
        colors: [],
        fontSize: '14px',
        fontWeight: 500,
      },
    }
  },
  yaxis: {
    labels:{
      style: {
        colors: [],
        fontSize: '14px',
        fontWeight: 500,
      },
    }
  },
  grid: {
    show: true,
    borderColor: 'rgba(var(--dark),.2)',
    strokeDashArray: 2,
    xaxis: {
      lines: {
        show: false
      }
    },
    yaxis: {
      lines: {
        show: true
      },
    }
  },
  tooltip: {
    x: {
      show: false,
    },
    style: {
      fontSize: '16px',
    },
  },
};

const heatmap1Chart = new ApexCharts(document.querySelector("#heatmap1"), heatmap1ChartOptions);
heatmap1Chart.render();

// **------ chart 2**
const data = [
  {
    name: 'W1',
    data: generateData(8, {
      min: 0,
      max: 90
    })
  },
  {
    name: 'W2',
    data: generateData(8, {
      min: 0,
      max: 90
    })
  },
  {
    name: 'W3',
    data: generateData(8, {
      min: 0,
      max: 90
    })
  },
  {
    name: 'W4',
    data: generateData(8, {
      min: 0,
      max: 90
    })
  },
  {
    name: 'W5',
    data: generateData(8, {
      min: 0,
      max: 90
    })
  },
  {
    name: 'W6',
    data: generateData(8, {
      min: 0,
      max: 90
    })
  },
  {
    name: 'W7',
    data: generateData(8, {
      min: 0,
      max: 90
    })
  },
  {
    name: 'W8',
    data: generateData(8, {
      min: 0,
      max: 90
    })
  },
  {
    name: 'W9',
    data: generateData(8, {
      min: 0,
      max: 90
    })
  },
  {
    name: 'W10',
    data: generateData(8, {
      min: 0,
      max: 90
    })
  },
  {
    name: 'W11',
    data: generateData(8, {
      min: 0,
      max: 90
    })
  },
  {
    name: 'W12',
    data: generateData(8, {
      min: 0,
      max: 90
    })
  },
  {
    name: 'W13',
    data: generateData(8, {
      min: 0,
      max: 90
    })
  },
  {
    name: 'W14',
    data: generateData(8, {
      min: 0,
      max: 90
    })
  },
  {
    name: 'W15',
    data: generateData(8, {
      min: 0,
      max: 90
    })
  }
]

data.reverse()

const colors = [getLocalStorageItem('color-primary','#0F626A'),getLocalStorageItem('color-secondary','#626262'),"#0AB964","#E14E5A","#F9C123","#4196FA","#C8B9D2","#28232D"]

colors.reverse()
const heatmap2ChartOptions = {
  series: data,
  chart: {
    fontFamily: "Rubik, serif",
    height: 450,
    type: 'heatmap',
  },
  dataLabels: {
    enabled: false
  },
  colors: colors,
  xaxis: {
    type: 'category',
    categories: ['10:00', '10:30', '11:00', '11:30', '12:00', '12:30', '01:00', '01:30'],
    labels:{
      style: {
        colors: [],
        fontSize: '14px',
        fontWeight: 500,
      },
    }
  },
  yaxis:{
    labels:{
      style: {
        colors: [],
        fontSize: '14px',
        fontWeight: 500,
      },
    }
  },

  title: {
    text: ''
  },
  grid: {
    padding: {
      right: 20
    }
  },
  tooltip: {
    x: {
      show: false,
    },
    style: {
      fontSize: '16px',
    },
  },
};

const heatmap2Chart = new ApexCharts(document.querySelector("#heatma2"), heatmap2ChartOptions);
heatmap2Chart.render();



//  **------chart 3**
const heatmap3ChartOptions = {
  series: [{
    name: 'Jan',
    data: generateData(20, {
      min: -30,
      max: 55
    })
  },
    {
      name: 'Feb',
      data: generateData(20, {
        min: -30,
        max: 55
      })
    },
    {
      name: 'Mar',
      data: generateData(20, {
        min: -30,
        max: 55
      })
    },
    {
      name: 'Apr',
      data: generateData(20, {
        min: -30,
        max: 55
      })
    },
    {
      name: 'May',
      data: generateData(20, {
        min: -30,
        max: 55
      })
    },
    {
      name: 'Jun',
      data: generateData(20, {
        min: -30,
        max: 55
      })
    },
    {
      name: 'Jul',
      data: generateData(20, {
        min: -30,
        max: 55
      })
    },
    {
      name: 'Aug',
      data: generateData(20, {
        min: -30,
        max: 55
      })
    },
    {
      name: 'Sep',
      data: generateData(20, {
        min: -30,
        max: 55
      })
    }
  ],
  chart: {
    fontFamily: "Rubik, serif",
    height: 350,
    type: 'heatmap',
  },
  plotOptions: {
    heatmap: {
      shadeIntensity: 0.5,
      radius: 0,
      useFillColorAsStroke: true,
      colorScale: {
        ranges: [{
          from: -30,
          to: 5,
          name: 'low',
          color: getLocalStorageItem('color-primary','#0F626A')
        },
          {
            from: 6,
            to: 20,
            name: 'medium',
            color: getLocalStorageItem('color-secondary','#626262')
          },
          {
            from: 21,
            to: 45,
            name: 'high',
            color: '#0AB964'
          },
          {
            from: 46,
            to: 55,
            name: 'extreme',
            color: '#E14E5A'
          }
        ]
      }
    }
  },
  dataLabels: {
    enabled: false
  },
  stroke: {
    width: 1
  },
  title: {
    text: ''
  },
  xaxis:{
    labels:{
      style: {
        colors: [],
        fontSize: '14px',
        fontWeight: 500,
      },
    }
  },
  yaxis:{
    labels:{
      style: {
        colors: [],
        fontSize: '14px',
        fontWeight: 500,
      },
    }
  },
  tooltip: {
    x: {
      show: false,
    },
    style: {
      fontSize: '16px',
    },
  },
};

const heatmap3Chart = new ApexCharts(document.querySelector("#heatma3"), heatmap3ChartOptions);
heatmap3Chart.render();

//  **------chart 4**
const heatmap4ChartOptions = {
  series: [{
    name: 'Metric1',
    data: generateData(20, {
      min: 0,
      max: 90
    })
  },

    {
      name: 'Metric2',
      data: generateData(20, {
        min: 0,
        max: 90
      })
    },

    {
      name: 'Metric3',
      data: generateData(20, {
        min: 0,
        max: 90
      })
    },

    {
      name: 'Metric4',
      data: generateData(20, {
        min: 0,
        max: 90
      })
    },

    {
      name: 'Metric5',
      data: generateData(20, {
        min: 0,
        max: 90
      })
    },
    {
      name: 'Metric6',
      data: generateData(20, {
        min: 0,
        max: 90
      })
    },
    {
      name: 'Metric7',
      data: generateData(20, {
        min: 0,
        max: 90
      })
    },
    {
      name: 'Metric8',
      data: generateData(20, {
        min: 0,
        max: 90
      })
    },
    {
      name: 'Metric8',
      data: generateData(20, {
        min: 0,
        max: 90
      })
    }
  ],
  chart: {
    fontFamily: "Rubik, serif",
    height: 350,
    type: 'heatmap',
  },
  stroke: {
    width: 0
  },
  plotOptions: {
    heatmap: {
      radius: 30,
      enableShades: false,
      colorScale: {
        ranges: [{
          from: 0,
          to: 50,
          color: '#F9C123'
        },
          {
            from: 51,
            to: 100,
            color: '#4196FA'
          },
        ],
      },

    }
  },
  dataLabels: {
    enabled: true,
    style: {
      colors: ['#fff']
    }
  },
  xaxis: {
    type: 'category',
    labels:{
      style: {
        colors: [],
        fontSize: '14px',
        fontWeight: 500,
      },
    }
  },
  yaxis:{
    labels:{
      style: {
        colors: [],
        fontSize: '14px',
        fontWeight: 500,
      },
    }
  },
  tooltip: {
    x: {
      show: false,
    },
    style: {
      fontSize: '16px',
    },
  },
};

const heatmap4Chart = new ApexCharts(document.querySelector("#heatma4"), heatmap4ChartOptions);
heatmap4Chart.render();
