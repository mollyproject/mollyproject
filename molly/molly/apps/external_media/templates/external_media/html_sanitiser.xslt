<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xsl:version="1.0">

  <xsl:template match="a|abbr|address|bdo|big|blockquote|br|caption|cite|code|col|colgroup|dd|del|div|dfn|dl|dt|em|h1|h2|h3|h4|h5|h6|hr|img|ins|kbd|li|ol|p|pre|q|samp|small|span|strong|sub|sup|table|tbody|td|tfoot|th|thead|tr|tt|ul|var">
    <xsl:copy>
      <xsl:apply-templates select="@* | node() | text()" />
    </xsl:copy>
  </xsl:template>
  
  <xsl:template match="text()">
    <xsl:copy/>
  </xsl:template>
  
  <xsl:template match="@dir | @class | @href | @id | @lang | @xml:lang | @title | @colspan | @rowspan | @src | @width | @height">
    <xsl:copy/>
  </xsl:template>
  
  <xsl:template match="@*"/>

<!--
  <xsl:template match="img">
    <img>
      <xsl:copy-of select="@src"/>
      <xsl:attribute name="externalmedia">src</xsl:attribute>
    </img>
  </xsl:template>
-->

</xsl:stylesheet>
