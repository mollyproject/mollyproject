<?xml version="1.0"?>
<xsl:stylesheet xsl:version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:molly="http://mollyproject.org/xpath#">
  <xsl:template match="/">
      <xsl:apply-templates select="*"/>
  </xsl:template>

  <!--
  <xsl:key name="headings" use="@level">
    <xsl:for-each select=".//*[matches(., '^h\d$')]">
      <xsl:sort/>
      <heading>
        <xsl<xsl:value-of select="string()"/>
    </xsl:for-each>
  </xsl:variable>
  -->

  <xsl:template match="text()">
    <xsl:copy/>
  </xsl:template>

  <xsl:template match="body">
    <xsl:copy>
      <xsl:apply-templates select="text() | * | @*"/>
    </xsl:copy>
  </xsl:template>

  <xsl:template match="img | ul | ol | li | em | strong | u | b | i | dl | dt | dd | table | thead | tbody | tfoot | tr | th | td | p | br | div | span | abbr | acronym | address | bda | blockquote | caption | cite | code | col | colgroup | del | dfn | hr | ins | kbd | pre | q | s | samp | small | big | strike | sub | sup | tt | var">
    <xsl:copy>
      <xsl:apply-templates select="text() | * | @*"/>
    </xsl:copy>
  </xsl:template>

  <!-- Add a prefix to @id attributes -->
  <xsl:template match="@id">
    <xsl:attribute name="id">{{ id_prefix }}-<xsl:value-of select="."/></xsl:attribute>
  </xsl:template>

  <xsl:template match="a[@href]">
    <xsl:choose>
      <xsl:when test="molly:safe-href(@href)">
        <a>
          <xsl:attribute name="rel">nofollow</xsl:attribute>
          <xsl:copy-of select="@href"/>
          <xsl:apply-templates select="node()"/>
        </a>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates select="node()"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>


  <!-- Attributes we believe are safe -->
  <xsl:template match="@src | @title | @alt | @width | @height | @dir | @lang | @xml:lang">
    <xsl:copy/>
  </xsl:template>

  <xsl:template match="@*"/>

  <!-- We want to suppress the contents of these -->
  <xsl:template match="script | object | style | applet"/>

  <!-- All other elements, drop the tag but keep the contents -->
  <xsl:template match="*">
    <xsl:apply-templates select="text() | * | @*"/>
  </xsl:template>

</xsl:stylesheet>
