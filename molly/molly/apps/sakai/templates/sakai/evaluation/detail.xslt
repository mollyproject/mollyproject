<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xsl:version="1.0">
  <xsl:template match="/">
    <evaluation>

      <title><xsl:value-of select=".//h3/span[2]"/></title>

      <instructions>
          <xsl:apply-templates select=".//div[@class='instruction']/span/node()"/>
      </instructions>

      <questions>
        <xsl:apply-templates select=".//form/node()"/>
      </questions>

      <submitButton>
        <xsl:variable name="input" select=".//div[@class='act']/input[@type='submit']"/>
        <input type="submit" name="{$input/@name}" value="Submit"/>
      </submitButton>

      <state>
        <xsl:variable name="alertMessage" select=".//div[@class='alertMessage']/text()"/>
        <xsl:choose>
          <xsl:when test="starts-with($alertMessage, 'Sorry!')">closed</xsl:when>
          <xsl:when test="starts-with($alertMessage, 'You do not')">forbidden</xsl:when>
          <xsl:otherwise>open</xsl:otherwise>
        </xsl:choose>
      </state>

      <state_message>
        <xsl:value-of select=".//div[@class='messageAlert']/ul/li/span"/>
      </state_message>

    </evaluation>
  </xsl:template>

  <xsl:template match="@style"/>
  <xsl:template match="div[@class='act']"/>

  <xsl:template match="@* | node()">
    <xsl:copy>
      <xsl:apply-templates select="@* | node()" />
    </xsl:copy>
  </xsl:template>

</xsl:stylesheet>
