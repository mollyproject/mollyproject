<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xsl:version="1.0">
  <xsl:template match="/">
    <evaluations>
      <xsl:apply-templates select=".//table"/>
    </evaluations>
  </xsl:template>

  <xsl:template match="@style"/>
  <xsl:template match="div[@class='act']"/>

  <xsl:template match="@* | node()">
    <xsl:copy>
      <xsl:apply-templates select="@* | node()" />
    </xsl:copy>
  </xsl:template>

  <xsl:template match="table">
    <evaluation>
      <xsl:apply-templates select="tr[2]/td[1]/a"/>
      <title><xsl:value-of select="tr[1]/th[1]"/></title>
      <xsl:choose>
        <xsl:when test="tr[2]/td[1]/a">
          <url><xsl:value-of select="tr[2]/td[1]/a/@href"/></url>
          <site><xsl:value-of select="tr[2]/td[1]/a"/></site>
        </xsl:when>
        <xsl:otherwise>
          <site><xsl:value-of select="tr[2]/td[1]/span"/></site>
        </xsl:otherwise>
      </xsl:choose>
      <status><xsl:value-of select="tr[2]/td[2]/span"/></status>
      <start><xsl:value-of select="tr[2]/td[3]/span"/></start>
      <end><xsl:value-of select="tr[2]/td[4]/span"/></end>
    </evaluation>
  </xsl:template>

</xsl:stylesheet>
