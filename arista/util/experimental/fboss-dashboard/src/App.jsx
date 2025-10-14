import React, { useState, memo } from 'react';
import './App.css';

const MIN_IFRAME_HEIGHT = 300;
const MAX_IFRAME_HEIGHT = 1500;
const HEIGHT_STEP = 100;

const pages = {
  home: {
    title: 'Home',
    description: 'Overview of Fboss Ship Report.',
    iframeUrl: 'https://go/fboss-shipreport',
  },
  odsViewer: {
    title: 'ODS Viewer',
    description: 'View ODS data through the embedded application.',
    iframeUrl: 'https://usercontent.sjc.aristanetworks.com/~deank/llm/ods_viewer.html',
  },
  showtechViewer: {
    title: 'Showtech Viewer',
    description: 'View Showtech data using the embedded viewer.',
    iframeUrl: null,
    externalLink: 'https://go/fboss-showtech',
  },
  ritsLatency: {
    title: 'RITS Latency',
    description: 'Analyze RITS latency per platforms.',
    iframeUrl:
      'https://docs.google.com/spreadsheets/d/1oi2JQXzzXuJ91JFhPd0xpw8_WLwz3Lg2Zeyqj7RyJTk/edit?usp=sharing',
  },
  escalations: {
    title: 'Escalations',
    description: 'Fboss escalations',
    iframeUrl: null,
    externalLink:
      'https://bb.infra.corp.arista.io/board/schedule/table/fboss-escalations',
  },
  cheatsheet: {
    title: 'Cheatsheet',
    description: 'Fboss developers cheatsheet',
    iframeUrl: 'https://go/fboss-cheatsheet',
  },
  benchmarks: {
    title: 'Benchmarks',
    description: 'WORK IN PROGRESS: fboss data is not yet recorded in benchmarkdb',
    iframes: [
      {
        name: 'Reboot times',
        url: 'https://benchmark.aristanetworks.com/?lineId=6&colorId=6&state=(lines=@((name=Viper&color=%230E57C2&benchmark=(regex=f&term=Fboss.Reboot.TotalTime.Viper)&filters=@()&id=1&visable&highlights=@()),(name=Whistler&color=%23FF51AC&benchmark=(regex=f&term=Fboss.Reboot.TotalTime.Whistler)&filters=@()&id=2&visable&highlights=@()),(name=Rackhawk&color=%238903d7&benchmark=(regex=f&term=Fboss.Reboot.TotalTime.Rackhawk)&filters=@()&id=3&visable&highlights=@()),(name=QuicksilverPFb&color=%23FF6E00&benchmark=(regex=f&term=Fboss.Reboot.TotalTime.QuicksilverPFb)&filters=@()&id=4&visable&highlights=@()),(name=RackhawkORv3&color=%2341a929&benchmark=(regex=f&term=Fboss.Reboot.TotalTime.RackhawkORv3)&filters=@()&id=5&visable&highlights=@()),(name=ViperB&color=%230e8fc2&benchmark=(regex=f&term=Fboss.Reboot.TotalTime.ViperB)&filters=@()&id=6&visable&highlights=@()))&highlights=@()&range=(type=rolling&days=30)&mode=abs&smoothing=f&version=~2&graphType=line)',
      },
      {
        name: 'Power cycle times',
        url: 'https://benchmark.aristanetworks.com/?lineId=6&colorId=6&state=(lines=@((name=Viper&color=%230E57C2&benchmark=(regex=f&term=Fboss.PowerCycle.TotalTime.Viper)&filters=@()&id=1&visable&highlights=@()),(name=Whistler&color=%23FF51AC&benchmark=(regex=f&term=Fboss.PowerCycle.TotalTime.Whistler)&filters=@()&id=2&visable&highlights=@()),(name=Rackhawk&color=%238903d7&benchmark=(regex=f&term=Fboss.PowerCycle.TotalTime.Rackhawk)&filters=@()&id=3&visable&highlights=@()),(name=QuicksilverPFb&color=%23FF6E00&benchmark=(regex=f&term=Fboss.PowerCycle.TotalTime.QuicksilverPFb)&filters=@()&id=4&visable&highlights=@()),(name=RackhawkORv3&color=%2341a929&benchmark=(regex=f&term=Fboss.PowerCycle.TotalTime.RackhawkORv3)&filters=@()&id=5&visable&highlights=@()),(name=ViperB&color=%230e8fc2&benchmark=(regex=f&term=Fboss.PowerCycle.TotalTime.ViperB)&filters=@()&id=6&visable&highlights=@()))&highlights=@()&range=(type=rolling&days=30)&mode=abs&smoothing=f&version=~2&graphType=line)',
      },
      {
        name: 'platform_manager warmup times',
        url: 'https://benchmark.aristanetworks.com/?lineId=6&colorId=6&state=(lines=@((name=Viper&color=%230E57C2&benchmark=(regex=f&term=Fboss.Service.PlatformManager.PostBootTime.Viper)&filters=@()&id=1&visable&highlights=@()),(name=Whistler&color=%23FF51AC&benchmark=(regex=f&term=Fboss.Service.PlatformManager.PostBootTime.Whistler)&filters=@()&id=2&visable&highlights=@()),(name=Rackhawk&color=%238903d7&benchmark=(regex=f&term=Fboss.Service.PlatformManager.PostBootTime.Rackhawk)&filters=@()&id=3&visable&highlights=@()),(name=QuicksilverPFb&color=%23FF6E00&benchmark=(regex=f&term=Fboss.Service.PlatformManager.PostBootTime.QuicksilverPFb)&filters=@()&id=4&visable&highlights=@()),(name=RackhawkORv3&color=%2341a929&benchmark=(regex=f&term=Fboss.Service.PlatformManager.PostBootTime.RackhawkORv3)&filters=@()&id=5&visable&highlights=@()),(name=ViperB&color=%230e8fc2&benchmark=(regex=f&term=Fboss.Service.PlatformManager.PostBootTime.ViperB)&filters=@()&id=6&visable&highlights=@()))&highlights=@()&range=(type=rolling&days=30)&mode=abs&smoothing=f&version=~2&graphType=line)',
      },
      {
        name: 'sw_agent / thrift warmup times',
        url: 'https://benchmark.aristanetworks.com/?lineId=6&colorId=6&state=(lines=@((name=Viper&color=%230E57C2&benchmark=(regex=f&term=Fboss.Service.SwAgent.PostBootTime.Viper)&filters=@()&id=1&visable&highlights=@()),(name=Whistler&color=%23FF51AC&benchmark=(regex=f&term=Fboss.Service.SwAgent.PostBootTime.Whistler)&filters=@()&id=2&visable&highlights=@()),(name=Rackhawk&color=%238903d7&benchmark=(regex=f&term=Fboss.Service.SwAgent.PostBootTime.Rackhawk)&filters=@()&id=3&visable&highlights=@()),(name=QuicksilverPFb&color=%23FF6E00&benchmark=(regex=f&term=Fboss.Service.SwAgent.PostBootTime.QuicksilverPFb)&filters=@()&id=4&visable&highlights=@()),(name=RackhawkORv3&color=%2341a929&benchmark=(regex=f&term=Fboss.Service.SwAgent.PostBootTime.RackhawkORv3)&filters=@()&id=5&visable&highlights=@()),(name=ViperB&color=%230e8fc2&benchmark=(regex=f&term=Fboss.Service.SwAgent.PostBootTime.ViperB)&filters=@()&id=6&visable&highlights=@()))&highlights=@()&range=(type=rolling&days=30)&mode=abs&smoothing=f&version=~2&graphType=line)',
      },
      {
        name: 'Link up times',
        url: 'https://benchmark.aristanetworks.com/?lineId=6&colorId=6&state=(lines=@((name=Viper&color=%230E57C2&benchmark=(regex=f&term=Fboss.LinkUp.PostBootTime.Viper)&filters=@()&id=1&visable&highlights=@()),(name=Whistler&color=%23FF51AC&benchmark=(regex=f&term=Fboss.LinkUp.PostBootTime.Whistler)&filters=@()&id=2&visable&highlights=@()),(name=Rackhawk&color=%238903d7&benchmark=(regex=f&term=Fboss.LinkUp.PostBootTime.Rackhawk)&filters=@()&id=3&visable&highlights=@()),(name=QuicksilverPFb&color=%23FF6E00&benchmark=(regex=f&term=Fboss.LinkUp.PostBootTime.QuicksilverPFb)&filters=@()&id=4&visable&highlights=@()),(name=RackhawkORv3&color=%2341a929&benchmark=(regex=f&term=Fboss.LinkUp.PostBootTime.RackhawkORv3)&filters=@()&id=5&visable&highlights=@()),(name=ViperB&color=%230e8fc2&benchmark=(regex=f&term=Fboss.LinkUp.PostBootTime.ViperB)&filters=@()&id=6&visable&highlights=@()))&highlights=@()&range=(type=rolling&days=30)&mode=abs&smoothing=f&version=~2&graphType=line)',
      },
      {
        name: 'fw_util times',
        url: 'https://benchmark.aristanetworks.com/?lineId=6&colorId=6&state=(lines=@((name=Viper&color=%230E57C2&benchmark=(regex=f&term=Fboss.FwUtil.TotalTime.Viper.All)&filters=@()&id=1&visable&highlights=@()),(name=Whistler&color=%23FF51AC&benchmark=(regex=f&term=Fboss.FwUtil.TotalTime.Whistler.All)&filters=@()&id=2&visable&highlights=@()),(name=Rackhawk&color=%238903d7&benchmark=(regex=f&term=Fboss.FwUtil.TotalTime.Rackhawk.All)&filters=@()&id=3&visable&highlights=@()),(name=QuicksilverPFb&color=%23FF6E00&benchmark=(regex=f&term=Fboss.FwUtil.TotalTime.QuicksilverPFb.All)&filters=@()&id=4&visable&highlights=@()),(name=RackhawkORv3&color=%2341a929&benchmark=(regex&term=Fboss.FwUtil.TotalTime.RackhawkORv3.All)&filters=@()&id=5&visable&highlights=@()),(name=ViperB&color=%230e8fc2&benchmark=(regex=f&term=Fboss.FwUtil.TotalTime.ViperB.All)&filters=@()&id=6&visable&highlights=@()))&highlights=@()&range=(type=rolling&days=30)&mode=abs&smoothing=f&version=~2&graphType=line)',
      },
    ],
  },
  fbossFeatures: {
    title: 'FBOSS Features Tracker',
    description:
      'Tracks feature development across all fboss supported platforms',
    iframeUrl: 'https://go/fboss-features',
  },
  openBmcFeatures: {
    title: 'OpenBMC Features Tracker',
    description:
      'Tracks feature development across all OpenBMC supported platforms',
    iframeUrl: 'https://go/openbmc-features',
  },
  references: {
    title: 'References',
    description:
      'Important links to Fboss related documents and spreadsheets.',
    iframeUrl: null,
    links: [
      { name: 'FBOSS OSS Platform Development Guide', url: 'https://aid/11233' },
      {
        name: 'DSF/7700 Meta RMA cases',
        url: 'https://docs.google.com/spreadsheets/d/1jRxrxJUuS8jp8cZazeCXq-G9fxaZfjdhPy63hwKY72g/edit?usp=sharing',
      },
      {
        name: 'Fboss Common Issues Tracker',
        url: 'https://go/fboss-common-issues',
      },
      {
        name: 'Fboss Escalation Watcher Rotation',
        url: 'https://go/fboss-rotation',
      },
      { name: 'FBOSS/OpenBMC Escalation Guide', url: 'https://aid/13460' },
      { name: 'FBOSS SCD Sub-System ID Tracker', url: 'go/fboss-scd-ids' },
    ],
  },
};

const IframeDisplay = memo(({ src, title, height }) => {
  return (
    <iframe
      src={src}
      title={title}
      width="100%"
      height={`${height}px`}
      allowFullScreen
      sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-top-navigation-by-user-activation"
    />
  );
});

const PageContent = ({
  pageKey,
  iframeHeight,
  onIncreaseIframeHeight,
  onReduceIframeHeight,
  isFullScreenMode,
  onToggleFullScreen,
  selectedIframeUrl,
  setSelectedIframeUrl,
}) => {
  const page = pages[pageKey];
  if (!page) return <div>Page not found.</div>;

  if (page.externalLink) {
    return (
      <div className="page-content">
        <h2>{page.title}</h2>
        <p>{page.description}</p>
        <p>
          This page redirects to an external application. If it did not open
          automatically, please click the link below:
        </p>
        <p>
          <a
            href={page.externalLink}
            target="_blank"
            rel="noopener noreferrer"
          >
            Open {page.title}
          </a>
        </p>
      </div>
    );
  }

  return (
    <div className="page-content">
      <div className="page-header">
        <div className="title-container">
          <h2>{page.title}</h2>
          <p>{page.description}</p>
        </div>
        {!isFullScreenMode && (page.iframeUrl || page.iframes) && (
          <div className="iframe-controls">
            <button
              onClick={onReduceIframeHeight}
              disabled={iframeHeight <= MIN_IFRAME_HEIGHT}
              className="iframe-height-button"
            >
              Reduce Height
            </button>
            <button
              onClick={onIncreaseIframeHeight}
              disabled={iframeHeight >= MAX_IFRAME_HEIGHT}
              className="iframe-height-button"
            >
              Increase Height
            </button>
            <button
              onClick={onToggleFullScreen}
              className="enter-fullscreen-button"
              title="Enter Full Screen"
            >
              ⤢
            </button>
          </div>
        )}
      </div>

      {(page.iframeUrl || page.iframes) && (
        <>
          {page.iframes && (
            <div className="iframe-sub-nav">
              {page.iframes.map((iframe, index) => (
                <button
                  key={index}
                  onClick={() => setSelectedIframeUrl(iframe.url)}
                  className={selectedIframeUrl === iframe.url ? 'active' : ''}
                >
                  {iframe.name}
                </button>
              ))}
            </div>
          )}
          <div className="iframe-container">
            <IframeDisplay
              key={pageKey}
              src={selectedIframeUrl}
              title={page.title}
              height={iframeHeight}
            />
          </div>
        </>
      )}

      {pageKey === 'references' && page.links && (
        <div className="references-list">
          <h3>Useful Links:</h3>
          <ul>
            {page.links.map((link, index) => (
              <li key={index}>
                <a href={link.url} target="_blank" rel="noopener noreferrer">
                  {link.name}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

function App() {
  const [currentPage, setCurrentPage] = useState('home');
  const [isSidebarHidden, setIsSidebarHidden] = useState(false);
  const [isFullScreenMode, setIsFullScreenMode] = useState(false);
  const [iframeHeight, setIframeHeight] = useState(900);
  const [selectedIframeUrl, setSelectedIframeUrl] = useState(pages.home.iframeUrl);

  // These handlers can also access the constants from the module scope now.
  const handleIncreaseIframeHeight = () => {
    setIframeHeight((prevHeight) => Math.min(prevHeight + HEIGHT_STEP, MAX_IFRAME_HEIGHT));
  };

  const handleReduceIframeHeight = () => {
    setIframeHeight((prevHeight) => Math.max(prevHeight - HEIGHT_STEP, MIN_IFRAME_HEIGHT));
  };

  const handleToggleFullScreen = () => {
    setIsFullScreenMode((prev) => !prev);
  };

  return (
    <div className={`dashboard-app ${isSidebarHidden ? 'sidebar-hidden' : ''} ${isFullScreenMode ? 'full-screen-mode' : ''}`}>
      <nav className="sidebar">
        <h1>Fboss Dashboard</h1>
        <ul>
          {Object.keys(pages).map((key) => (
            <li key={key}>
              <button
                onClick={() => {
                  if (pages[key].externalLink) {
                    window.open(pages[key].externalLink, '_blank');
                  } else {
                    setCurrentPage(key);
                    if (pages[key].iframes) {
                      setSelectedIframeUrl(pages[key].iframes[0].url);
                    } else if (pages[key].iframeUrl) {
                      setSelectedIframeUrl(pages[key].iframeUrl);
                    }
                  }
                }}
                className={!pages[key].externalLink && currentPage === key ? 'active' : ''}
              >
                {pages[key].title}
              </button>
            </li>
          ))}
        </ul>
        <button
          className="hide-menu-button bottom-aligned"
          onClick={() => setIsSidebarHidden(!isSidebarHidden)}
          title={isSidebarHidden ? 'Show Menu' : 'Hide Menu'}
        >
          {isSidebarHidden ? '☰ Show Menu' : '< Hide Menu'}
        </button>
      </nav>

      <main className="content">
        {isSidebarHidden && !isFullScreenMode && (
          <button
            className="show-menu-button-float"
            onClick={() => setIsSidebarHidden(false)}
            title="Show Menu"
          >
            ☰
          </button>
        )}

        {isFullScreenMode && pages[currentPage].iframeUrl && (
          <button
            onClick={handleToggleFullScreen}
            className="exit-fullscreen-button"
            title="Exit Full Screen"
          >
            ⛶
          </button>
        )}
        
        <PageContent
          pageKey={currentPage}
          iframeHeight={iframeHeight}
          onIncreaseIframeHeight={handleIncreaseIframeHeight}
          onReduceIframeHeight={handleReduceIframeHeight}
          isFullScreenMode={isFullScreenMode}
          onToggleFullScreen={handleToggleFullScreen}
          selectedIframeUrl={selectedIframeUrl}
          setSelectedIframeUrl={setSelectedIframeUrl}
        />
      </main>
    </div>
  );
}

export default App;