import React from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import {CodeBlock} from './LessonWidgets.jsx';
import {assetUrl,splitWidgets} from '../lib/book.js';
import {pageHref} from '../lib/navigation.js';

export default function BookMarkdown({source,pageId,widgets={},imageDimensions={},imageVariants={}}){
  const components={
    a:({href='',children})=>{
      const [linkedPage,linkedSection]=href.replace(/^#\//,'').split('/');
      const url=href.startsWith('#/')?pageHref(linkedPage,linkedSection):href.startsWith('#')?pageHref(pageId,href.slice(1)):assetUrl(href);
      const external=/^https?:/.test(url);
      return <a href={url} {...(external?{target:'_blank',rel:'noreferrer'}:{})} {...(/\.(excalidraw|csv)$/.test(href)?{download:true}:{})}>{children}</a>;
    },
    img:({src,alt})=>{
      const variant=imageVariants[src];
      const image=<img className={'content-image'+(variant?' lesson-diagram':'')} src={assetUrl(src||'')} alt={alt||''} loading="lazy" decoding="async" width={variant?.width||imageDimensions[src]?.[0]} height={variant?.height||imageDimensions[src]?.[1]}/>;
      return variant?<picture className="lesson-visual"><source media="(max-width:700px)" srcSet={assetUrl(variant.mobile)} width={variant.mobileWidth} height={variant.mobileHeight}/>{image}</picture>:image;
    },
    blockquote:({node,children})=>{
      const illustrated=node.children.some(child=>child.tagName==='p'&&child.children?.some(item=>item.tagName==='img'&&String(item.properties?.src).includes('images/quantara-story-')));
      return illustrated?<aside className="quantara-story" aria-label="นิทานจาก Quantara">{children}</aside>:<blockquote>{children}</blockquote>;
    },
    table:({children})=><div className="table-scroll"><table>{children}</table></div>,
    pre:({children})=>{
      const child=React.Children.toArray(children)[0];
      const language=child?.props?.className?.replace('language-','')||'text';
      return <CodeBlock code={String(child?.props?.children||'').replace(/\n$/,'')} title={language==='shell'?'Terminal':language.toUpperCase()} language={language}/>;
    },
  };
  return <>{splitWidgets(source).map((part,i)=>part.widget
    ? <React.Fragment key={i}>{widgets[part.widget]||<p className="content-error">Unknown content block: {part.widget}</p>}</React.Fragment>
    : <div className="markdown" key={i}><Markdown remarkPlugins={[remarkGfm,remarkMath]} rehypePlugins={[[rehypeKatex,{strict:'ignore',trust:false}]]} components={components}>{part.markdown}</Markdown></div>)}</>;
}
